from app.orchestration.normalize import coerce_to_str, normalize_for_model
from app.orchestration.state import ProductBlueprintOutput, SolutionArchitectureOutput


def test_coerce_list_to_string():
    assert coerce_to_str(["Axios", "Chart.js"]) == "Axios, Chart.js"


def test_coerce_dict_to_string():
    value = {"capacity": "5000 users", "detail": "Medium universities"}
    assert "capacity: 5000 users" in coerce_to_str(value)


def test_normalize_architecture_step_type_mismatches():
    raw = {
        "overview": "Architecture",
        "architecture_style": "modular monolith",
        "components": [],
        "stack": [{"layer": "frontend", "supportingTools": ["Axios", "Chart.js"]}],
        "entities": [],
        "relationships": [],
        "api_integrations": [],
        "security_controls": [],
        "quality_attributes": [],
        "deployment_topology": [],
    }

    validated = SolutionArchitectureOutput.model_validate(normalize_for_model(raw, SolutionArchitectureOutput))
    assert validated.stack[0]["supportingTools"] == "Axios, Chart.js"


def test_product_blueprint_schema_accepts_empty_optional_collections():
    validated = ProductBlueprintOutput.model_validate({"overview": "Brief", "problem_statement": "Problem"})
    assert validated.functional == []


def test_normalize_trims_ai_lists_to_schema_limit():
    raw = {
        "overview": "Brief",
        "problem_statement": "Problem",
        "business_objectives": [f"Objective {index}" for index in range(7)],
    }
    validated = ProductBlueprintOutput.model_validate(normalize_for_model(raw, ProductBlueprintOutput))
    assert len(validated.business_objectives) == 5
