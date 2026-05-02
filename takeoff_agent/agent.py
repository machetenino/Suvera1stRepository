"""Core AI take-off agent — agentic loop powered by Claude tool use."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import anthropic

from .processors.image_processor import load_drawing, prepare_for_api
from .tools import TOOLS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert architectural estimator and quantity surveyor specialising in construction take-offs from architectural drawings.

Your role is to analyse architectural drawings provided as images and extract precise quantities for construction estimation. You work methodically and leave nothing out.

## Current scope
- **Partition plans**: wall type quantities in linear feet only
- **Reflected Ceiling Plans (RCP)**: ceiling type quantities in square feet only
- Architectural legends, schedules, and keynotes
- Drawing scales and dimension interpretation

## Workflow — follow this order strictly
1. Call **classify_drawing** — identify type, scale, title block, and legends present
2. Call the matching extraction tool:
   - Partition plan → **extract_partition_data** (wall types + LF)
   - Reflected ceiling plan → **extract_rcp_data** (ceiling types + SF)
   - Unknown/other → use the closest match and note it
3. (Optional) Call **request_region_analysis** for any unclear area
4. Call **finalize_takeoff** — compile the complete, structured take-off

## Measurement principles
- **Linear measurements** (walls): trace each wall type across the drawing using the scale; note the method → confidence = medium
- **Area estimates** (ceilings): derive from room/zone extents using the scale → confidence = medium
- When scale is unclear, state that explicitly and mark confidence = low
- Work left→right, top→bottom to avoid missing any zones or wall runs

## Quality standards
- **High confidence**: precisely scale-measured with a clear scale bar
- **Medium confidence**: estimated from visual proportions using the noted scale
- **Low confidence**: inferred, partially obscured, or scale unknown
- Always report the measurement basis in measurement_notes
- Flag verification items rather than guessing silently"""


@dataclass
class TakeoffResult:
    drawing_path: str
    drawing_type: str
    scale: str
    title_block: dict
    line_items: list[dict]
    verification_items: list[str]
    overall_confidence: str
    estimator_notes: str
    raw_data: dict = field(default_factory=dict)


class TakeoffAgent:
    """
    Runs an agentic take-off analysis on a single architectural drawing.

    Uses Claude with tool use to classify the drawing, extract quantities,
    and compile a structured take-off report.
    """

    def __init__(self, model: str = "claude-sonnet-4-6", max_iterations: int = 12):
        self.client = anthropic.Anthropic()
        self.model = model
        self.max_iterations = max_iterations

    def analyze_drawing(
        self,
        image_path: str | Path,
        verbose: bool = False,
        enhance_image: bool = True,
    ) -> TakeoffResult:
        """
        Perform a complete take-off analysis on an architectural drawing.

        Args:
            image_path: Path to a PDF or image file.
            verbose: Enable debug logging.
            enhance_image: Apply contrast/sharpness enhancement before analysis.

        Returns:
            TakeoffResult with all extracted quantities and metadata.
        """
        if verbose:
            logging.basicConfig(level=logging.DEBUG)

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Drawing not found: {path}")

        images = load_drawing(path)
        if not images:
            raise ValueError(f"No images could be loaded from: {path}")

        # For now use the first page; multi-page support added via analyze_drawing_set
        image_source = prepare_for_api(images[0], enhance_contrast=enhance_image)

        collected: dict = {}
        result = self._run_loop(image_source, str(path), collected, verbose)
        return result

    def analyze_drawing_set(
        self,
        pdf_path: str | Path,
        verbose: bool = False,
        enhance_image: bool = True,
    ) -> list[TakeoffResult]:
        """
        Analyse every page of a multi-page PDF (a drawing set).
        Returns one TakeoffResult per page.
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"Drawing set not found: {path}")

        images = load_drawing(path)
        results = []
        for page_num, image in enumerate(images, start=1):
            logger.info(f"Analysing page {page_num}/{len(images)}")
            image_source = prepare_for_api(image, enhance_contrast=enhance_image)
            collected: dict = {}
            page_path = f"{path} (page {page_num})"
            result = self._run_loop(image_source, page_path, collected, verbose)
            results.append(result)
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_loop(
        self,
        image_source: dict,
        drawing_path: str,
        collected: dict,
        verbose: bool,
    ) -> TakeoffResult:
        messages: list[dict] = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            **image_source,
                            # Cache the image — subsequent turns reuse the cached token
                            "cache_control": {"type": "ephemeral"},
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Please perform a complete construction take-off on this architectural drawing. "
                            "Follow your workflow: classify the drawing, extract all quantities, "
                            "then call finalize_takeoff to produce the final structured report. "
                            "Be thorough — missing items cause cost overruns."
                        ),
                    },
                ],
            }
        ]

        for iteration in range(self.max_iterations):
            if verbose:
                logger.debug(f"Agent iteration {iteration + 1}/{self.max_iterations}")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=8096,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        # Cache the (large) system prompt across all turns
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=TOOLS,
                messages=messages,
            )

            if verbose:
                logger.debug(f"Stop reason: {response.stop_reason}")

            # Collect tool calls and build results list
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    if verbose:
                        logger.debug(f"Tool called: {block.name}")
                    collected[block.name] = block.input
                    feedback = self._tool_feedback(block.name, block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(feedback),
                        }
                    )

            # Done when the model stops on its own or finalize has been called
            if response.stop_reason == "end_turn" or not tool_results:
                break

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

            if "finalize_takeoff" in collected:
                break

        return self._build_result(drawing_path, collected)

    def _tool_feedback(self, tool_name: str, tool_input: dict) -> dict:
        """Return a short feedback message for each tool call."""
        if tool_name == "classify_drawing":
            dtype = tool_input.get("drawing_type", "unknown")
            scale = tool_input.get("scale", "not found")
            return {
                "status": "ok",
                "message": (
                    f"Classified as '{dtype}', scale '{scale}'. "
                    "Now extract quantities using the matching extraction tool."
                ),
            }

        if tool_name == "extract_partition_data":
            walls = len(tool_input.get("walls", []))
            lf = tool_input.get("total_wall_lf", 0)
            return {
                "status": "ok",
                "message": (
                    f"Captured {walls} wall type(s), {lf:.0f} LF total. "
                    "Call finalize_takeoff to compile the report."
                ),
            }

        if tool_name == "extract_rcp_data":
            ceilings = len(tool_input.get("ceiling_types", []))
            area = tool_input.get("total_ceiling_area_sf", 0)
            return {
                "status": "ok",
                "message": (
                    f"Captured {ceilings} ceiling type(s), {area:.0f} SF total. "
                    "Call finalize_takeoff to compile the report."
                ),
            }

        if tool_name == "request_region_analysis":
            return {
                "status": "ok",
                "message": (
                    "Region noted. Examine the full drawing image provided and "
                    "incorporate your findings into the extraction tool call."
                ),
            }

        if tool_name == "finalize_takeoff":
            items = len(tool_input.get("line_items", []))
            return {"status": "complete", "message": f"Take-off complete — {items} line item(s)."}

        return {"status": "ok"}

    def _build_result(self, drawing_path: str, collected: dict) -> TakeoffResult:
        classification = collected.get("classify_drawing", {})
        finalized = collected.get("finalize_takeoff", {})

        line_items = finalized.get("line_items", [])
        if not line_items:
            # finalize_takeoff wasn't called — construct items from raw extracted data
            line_items = self._items_from_raw(collected)

        return TakeoffResult(
            drawing_path=drawing_path,
            drawing_type=classification.get("drawing_type", "unknown"),
            scale=classification.get("scale") or "not determined",
            title_block=classification.get("title_block") or {},
            line_items=line_items,
            verification_items=finalized.get("verification_items") or [],
            overall_confidence=finalized.get("overall_confidence") or "medium",
            estimator_notes=finalized.get("estimator_notes") or "",
            raw_data=collected,
        )

    def _items_from_raw(self, collected: dict) -> list[dict]:
        """Fallback: assemble line items directly from raw extraction data."""
        items: list[dict] = []

        for wall in collected.get("extract_partition_data", {}).get("walls", []):
            items.append(
                {
                    "category": "Partitions",
                    "item_code": wall.get("type_id", ""),
                    "description": wall.get("description") or wall.get("type_id", ""),
                    "quantity": wall.get("estimated_linear_feet", 0),
                    "unit": "LF",
                    "confidence": "medium",
                    "notes": wall.get("notes", ""),
                }
            )

        for ceiling in collected.get("extract_rcp_data", {}).get("ceiling_types", []):
            items.append(
                {
                    "category": "Ceilings",
                    "item_code": ceiling.get("type_id", ""),
                    "description": ceiling.get("description", ""),
                    "quantity": ceiling.get("estimated_area_sf", 0),
                    "unit": "SF",
                    "confidence": "medium",
                    "notes": ceiling.get("notes", ""),
                }
            )

        return items
