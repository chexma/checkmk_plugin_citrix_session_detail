#!/usr/bin/env python3
"""Rulesets for Citrix Session Detail plugin.

Provides:
- CheckParameters for citrix_session_count thresholds
- AgentConfig for bakery deployment with MaxRecordCount setting
"""

from cmk.rulesets.v1 import Help, Title
from cmk.rulesets.v1.form_specs import (
    DefaultValue,
    DictElement,
    Dictionary,
    Integer,
    LevelDirection,
    SimpleLevels,
    TimeSpan,
    TimeMagnitude,
)
from cmk.rulesets.v1.rule_specs import AgentConfig, CheckParameters, HostCondition, Topic


def _check_parameter_form():
    return Dictionary(
        title=Title("Citrix Session Count Parameters"),
        elements={
            "active_levels": DictElement(
                required=False,
                parameter_form=SimpleLevels(
                    title=Title("Active session levels"),
                    help_text=Help("Upper levels for the number of active sessions"),
                    form_spec_template=Integer(),
                    level_direction=LevelDirection.UPPER,
                    prefill_fixed_levels=DefaultValue(value=(20, 30)),
                ),
            ),
            "disconnected_levels": DictElement(
                required=False,
                parameter_form=SimpleLevels(
                    title=Title("Disconnected session levels"),
                    help_text=Help("Upper levels for the number of disconnected sessions"),
                    form_spec_template=Integer(),
                    level_direction=LevelDirection.UPPER,
                    prefill_fixed_levels=DefaultValue(value=(5, 10)),
                ),
            ),
            "disconnected_age_levels": DictElement(
                required=False,
                parameter_form=SimpleLevels(
                    title=Title("Oldest disconnected session age"),
                    help_text=Help("Upper levels for the age of the oldest disconnected session"),
                    form_spec_template=TimeSpan(
                        displayed_magnitudes=[TimeMagnitude.DAY, TimeMagnitude.HOUR],
                    ),
                    level_direction=LevelDirection.UPPER,
                    prefill_fixed_levels=DefaultValue(value=(86400.0, 259200.0)),
                ),
            ),
        },
    )


rule_spec_citrix_session_count = CheckParameters(
    name="citrix_session_count",
    title=Title("Citrix Session Count"),
    topic=Topic.APPLICATIONS,
    parameter_form=_check_parameter_form,
    condition=HostCondition(),
)


def _agent_config_form():
    return Dictionary(
        title=Title("Citrix Session Detail"),
        elements={
            "max_record_count": DictElement(
                required=False,
                parameter_form=Integer(
                    title=Title("Maximum number of sessions to query"),
                    help_text=Help(
                        "Maximum number of sessions returned by Get-BrokerSession. "
                        "Increase if you have more sessions in your environment."
                    ),
                    prefill=DefaultValue(500),
                ),
            ),
        },
    )


rule_spec_citrix_session_detail_bakery = AgentConfig(
    name="citrix_session_detail",
    title=Title("Citrix Session Detail"),
    topic=Topic.APPLICATIONS,
    parameter_form=_agent_config_form,
)
