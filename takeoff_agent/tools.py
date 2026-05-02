"""Tool definitions for the architectural take-off agent."""

TOOLS = [
    {
        "name": "classify_drawing",
        "description": (
            "Analyze the drawing image and classify its type. "
            "Identify the drawing type, extract title block information, "
            "find the scale, and describe what legend/schedule information is visible. "
            "Always call this first for any new drawing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "drawing_type": {
                    "type": "string",
                    "enum": [
                        "partition_plan",
                        "reflected_ceiling_plan",
                        "floor_plan",
                        "electrical_plan",
                        "plumbing_plan",
                        "mechanical_plan",
                        "structural_plan",
                        "site_plan",
                        "elevation",
                        "section",
                        "detail",
                        "schedule",
                        "unknown",
                    ],
                    "description": "The type of architectural drawing",
                },
                "scale": {
                    "type": "string",
                    "description": (
                        "Drawing scale as noted in title block or on drawing "
                        "(e.g., '1/8\" = 1\\'0\"', '1:100', '1/4\" = 1\\'0\"', 'NTS')"
                    ),
                },
                "title_block": {
                    "type": "object",
                    "properties": {
                        "project_name": {"type": "string"},
                        "drawing_number": {"type": "string"},
                        "drawing_title": {"type": "string"},
                        "date": {"type": "string"},
                        "revision": {"type": "string"},
                        "north_arrow_present": {"type": "boolean"},
                    },
                },
                "legends_and_schedules": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of legends, schedules, keynotes, and symbol definitions visible",
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Confidence in classification (0-1)",
                },
                "notes": {
                    "type": "string",
                    "description": "Relevant observations about drawing quality, content, or issues",
                },
            },
            "required": ["drawing_type", "confidence"],
        },
    },
    {
        "name": "extract_partition_data",
        "description": (
            "Extract wall type quantities from a partition plan drawing. "
            "Identify each wall type from the legend, then estimate the total linear footage "
            "of each type by tracing it across the drawing using the noted scale."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "walls": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type_id": {
                                "type": "string",
                                "description": "Wall type ID from legend (e.g., 'WT-1', 'Type A', 'EXT-1', 'P-1')",
                            },
                            "description": {
                                "type": "string",
                                "description": (
                                    "Full construction description "
                                    "(e.g., '3-5/8\" 20ga Metal Stud @ 16\" OC, 5/8\" GWB each side')"
                                ),
                            },
                            "estimated_linear_metres": {
                                "type": "number",
                                "description": "Estimated total linear metres (LM) of this wall type in the drawing",
                            },
                            "height": {
                                "type": "string",
                                "description": "Wall height if noted (e.g., '9\\'-0\" AFF', 'Full height to deck')",
                            },
                            "fire_rating": {
                                "type": "string",
                                "description": "Fire rating if applicable (e.g., '1-hr UL Design', '2-hr', 'N/A')",
                            },
                            "quantity_method": {
                                "type": "string",
                                "enum": ["measured_from_scale", "estimated", "partial_view"],
                                "description": "How the quantity was determined",
                            },
                            "notes": {"type": "string"},
                        },
                        "required": ["type_id", "estimated_linear_metres", "quantity_method"],
                    },
                },
                "total_wall_lm": {
                    "type": "number",
                    "description": "Sum of all wall type linear metres",
                },
                "measurement_notes": {
                    "type": "string",
                    "description": "How measurements were derived and their accuracy level",
                },
            },
            "required": ["walls", "total_wall_lm"],
        },
    },
    {
        "name": "extract_rcp_data",
        "description": (
            "Extract ceiling type quantities from a Reflected Ceiling Plan (RCP). "
            "Identify each ceiling type from the legend, then estimate the area of each type "
            "by measuring the zones shown on the drawing using the noted scale."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ceiling_types": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type_id": {"type": "string"},
                            "description": {
                                "type": "string",
                                "description": (
                                    "e.g., '2x4 Acoustic Ceiling Tile (ACT)', "
                                    "'Gypsum Wallboard (GWB)', 'Open to Structure', "
                                    "'Wood Plank', '2x2 ACT'"
                                ),
                            },
                            "estimated_area_m2": {"type": "number", "description": "Estimated area in square metres (m²)"},
                            "height_aff": {
                                "type": "string",
                                "description": "Ceiling height above finished floor (e.g., '9\\'-0\"', '10\\'-0\"')",
                            },
                            "notes": {"type": "string"},
                        },
                        "required": ["description", "estimated_area_sf"],
                    },
                },
                "total_ceiling_area_m2": {
                    "type": "number",
                    "description": "Total ceiling area in square metres (m²) across all ceiling types",
                },
                "measurement_notes": {
                    "type": "string",
                    "description": "How areas were derived",
                },
            },
            "required": ["ceiling_types", "total_ceiling_area_m2"],
        },
    },
    {
        "name": "request_region_analysis",
        "description": (
            "Flag a specific region of the drawing for closer examination. "
            "Use this when you need to call out a dense or unclear area "
            "that warrants extra attention in your analysis."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "region_description": {
                    "type": "string",
                    "description": "Where on the drawing (e.g., 'legend bottom-right', 'NW quadrant dense fixture area')",
                },
                "analysis_goal": {
                    "type": "string",
                    "description": "What information is needed from this region",
                },
                "findings": {
                    "type": "string",
                    "description": "What you can observe in this region from the full image",
                },
            },
            "required": ["region_description", "analysis_goal"],
        },
    },
    {
        "name": "finalize_takeoff",
        "description": (
            "Compile the complete take-off report. "
            "Call this after all data has been extracted. "
            "Consolidate all findings into a structured, line-item take-off list. "
            "This must be the last tool call."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "drawing_summary": {
                    "type": "string",
                    "description": "One or two sentence description of what was analyzed",
                },
                "line_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": (
                                    "e.g., 'Partitions', 'Doors & Hardware', "
                                    "'Light Fixtures', 'HVAC', 'Fire Protection', "
                                    "'Life Safety', 'Ceilings', 'Openings'"
                                ),
                            },
                            "item_code": {
                                "type": "string",
                                "description": "Type mark or code (e.g., 'WT-1', 'L-1', 'D-01')",
                            },
                            "description": {
                                "type": "string",
                                "description": "Full description of the item",
                            },
                            "quantity": {"type": "number"},
                            "unit": {
                                "type": "string",
                                "description": "LM (linear metres), EA, m² (square metres), etc.",
                            },
                            "confidence": {
                                "type": "string",
                                "enum": ["high", "medium", "low"],
                                "description": (
                                    "high=directly counted or scale-measured; "
                                    "medium=estimated from context; "
                                    "low=inferred or partially obscured"
                                ),
                            },
                            "notes": {"type": "string"},
                        },
                        "required": ["category", "description", "quantity", "unit", "confidence"],
                    },
                },
                "verification_items": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Items that should be field-verified or confirmed against specs",
                },
                "overall_confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                },
                "estimator_notes": {
                    "type": "string",
                    "description": "Important caveats, assumptions, or guidance for the estimator reviewing this take-off",
                },
            },
            "required": ["drawing_summary", "line_items", "overall_confidence"],
        },
    },
]
