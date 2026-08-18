from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AnalysisEvidence(BaseModel):
    """一条与数据摘要中的类别和指标精确对应的证据。"""

    model_config = ConfigDict(extra="forbid")

    category: str = Field(min_length=1, description="摘要中的原始类别名称")
    field: Literal["样本数", "平均血糖水平"] = Field(
        description="类别汇总中的指标名称"
    )
    value: str = Field(min_length=1, description="该类别和指标对应的原始值")


class AnalysisResult(BaseModel):
    """数据摘要解读的固定输出结构。"""

    model_config = ConfigDict(extra="forbid")

    conclusion: str = Field(min_length=1, description="基于摘要的结论")
    evidence: list[AnalysisEvidence] = Field(
        min_length=1,
        description="支持结论的证据列表",
    )
    limitations: list[str] = Field(
        min_length=1,
        description="证据边界或数据限制",
    )
    next_step: str = Field(min_length=1, description="下一步建议")
