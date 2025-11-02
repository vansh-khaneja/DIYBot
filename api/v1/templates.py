"""
Templates API endpoints for managing workflow templates.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import os
import json
from pathlib import Path

from db import get_connection, USING_POSTGRES

router = APIRouter(prefix="/templates", tags=["templates"])

# Base templates directory (now in backend folder)
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


@router.get("/", response_model=List[Dict[str, Any]])
async def list_templates():
    """
    List all available workflow templates from the templates directory.

    Returns a list of templates with their metadata:
    - name: Template name (from folder name)
    - description: Template description (from workflow.json)
    - category: Template category (from folder name)
    - workflow: Complete workflow data
    - path: Relative path to the template
    """
    templates = []

    # Ensure templates directory exists
    if not TEMPLATES_DIR.exists():
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        return templates

    # Scan all subdirectories in templates folder
    for template_folder in TEMPLATES_DIR.iterdir():
        if not template_folder.is_dir():
            continue

        # Look for workflow.json in each folder
        workflow_file = template_folder / "workflow.json"

        if not workflow_file.exists():
            continue

        try:
            # Read and parse the workflow JSON
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)

            # Extract metadata
            template_info = {
                "name": workflow_data.get("name", template_folder.name),
                "description": workflow_data.get("description", f"Template: {template_folder.name}"),
                "category": template_folder.name,
                "workflow": workflow_data,
                "path": str(template_folder.relative_to(TEMPLATES_DIR))
            }

            templates.append(template_info)

        except json.JSONDecodeError as e:
            print(f"Error parsing {workflow_file}: {e}")
            continue
        except Exception as e:
            print(f"Error reading template from {template_folder}: {e}")
            continue

    return templates


@router.get("/{category}", response_model=Dict[str, Any])
async def get_template(category: str):
    """
    Get a specific template by category name.

    Args:
        category: The template category (folder name)

    Returns:
        Template data including workflow JSON
    """
    template_folder = TEMPLATES_DIR / category

    if not template_folder.exists() or not template_folder.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"Template category '{category}' not found"
        )

    workflow_file = template_folder / "workflow.json"

    if not workflow_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No workflow.json found in template '{category}'"
        )

    try:
        with open(workflow_file, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)

        return {
            "name": workflow_data.get("name", category),
            "description": workflow_data.get("description", f"Template: {category}"),
            "category": category,
            "workflow": workflow_data,
            "path": str(template_folder.relative_to(TEMPLATES_DIR))
        }

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON in template: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading template: {str(e)}"
        )


@router.post("/{category}/create-workflow")
async def create_workflow_from_template(category: str, workflow_name: str = None):
    """
    Create a new workflow in the database from a template.

    Args:
        category: The template category
        workflow_name: Optional custom name for the new workflow

    Returns:
        Created workflow data with ID
    """
    import uuid

    # Get the template
    template = await get_template(category)

    # Prepare workflow data
    workflow_data = template["workflow"]

    # Use custom name if provided, otherwise use template name
    name = workflow_name if workflow_name else f"{template['name']} (Copy)"

    # Create the workflow
    try:
        workflow_id = str(uuid.uuid4())
        with get_connection() as conn:
            query = (
                "INSERT INTO workflows (id, name, data_json) VALUES (%s, %s, %s)"
                if USING_POSTGRES
                else "INSERT INTO workflows (id, name, data_json) VALUES (?, ?, ?)"
            )
            conn.execute(query, (workflow_id, name, json.dumps(workflow_data)))
            if not USING_POSTGRES:
                conn.commit()

        return {
            "id": workflow_id,
            "name": name,
            "message": f"Workflow created from template '{category}'"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating workflow from template: {str(e)}"
        )
