from semantic_reasoning_agent.schemas.orchestration import (
    OrchestrationConfigSchema,
    default_orchestration_config,
)


def test_default_orchestration_config_is_legacy_mode() -> None:
    config = default_orchestration_config()
    assert config.mode == "legacy_static_plan"
    assert config.orchestrator.strategy == "legacy_static_plan"
    assert config.orchestrator.enabled is True
    assert config.stop_policy.max_iterations == 4


def test_orchestration_config_accepts_react_mode() -> None:
    config = OrchestrationConfigSchema.model_validate(
        {
            "version": "1.0",
            "mode": "react_two_agent",
            "orchestrator": {
                "strategy": "react_two_agent",
                "enabled": True,
            },
            "stop_policy": {"max_iterations": 6},
        }
    )
    assert config.mode == "react_two_agent"
    assert config.orchestrator.strategy == "react_two_agent"
    assert config.stop_policy.max_iterations == 6

