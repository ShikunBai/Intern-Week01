from pydantic import BaseModel, ConfigDict, Field


class AnalysisEvidence(BaseModel):
    """一条可在数据摘要中复核的证据。"""

    model_config = ConfigDict(extra="forbid")

    metric: str = Field(min_length=1, description="证据对应的指标或类别说明")
    value: str = Field(min_length=1, description="证据对应的数值或文本值")


class AnalysisResult(BaseModel):
    """数据摘要解读的固定输出结构。"""

    model_config = ConfigDict(extra="forbid")

    conclusion: str = Field(min_length=1, description="基于摘要的结论")
    evidence: list[AnalysisEvidence] = Field(description="支持结论的证据列表")
    limitations: list[str] = Field(description="证据边界或数据限制")
    next_step: str = Field(min_length=1, description="下一步建议")
