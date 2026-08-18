# 离线测试结果

## 执行命令

```bash
python -m pytest tests/ -v
```
## 最终结果
4 passed

## 四个离线测试

1. `test_summary_contains_correct_group_metrics`

   验证 pandas 摘要的总行数、缺失数、`Govt_job` 的样本数和平均血糖水平正确。

2. `test_normal_structured_response_parses_without_real_api`

   使用假客户端模拟正常 JSON 响应，验证其可解析为 `AnalysisResult`；并验证每条证据包含 `category`、`field` 和 `value`，请求使用 JSON Output 与非流式模式。

3. `test_insufficient_evidence_response_states_limitations`

   使用假客户端模拟证据不足场景，验证结论和限制明确说明证据不足。该测试还验证证据的“类别、指标、数值”必须精确对应 `summary.json`：即使 `112.65` 存在于摘要中，若被错误写成 `Private` 的样本数，程序也必须拒绝该结果。

4. `test_api_connection_failure_does_not_leak_configuration`

   使用 `httpx.Request` 模拟 API 连接失败，验证程序返回受控错误，且错误输出不泄露模拟密钥。

## 真实测试输出

    collected 4 items

    tests/test_data_summary.py::test_summary_contains_correct_group_metrics PASSED [ 25%]
    tests/test_interpreter.py::test_normal_structured_response_parses_without_real_api PASSED [ 50%]
    tests/test_interpreter.py::test_insufficient_evidence_response_states_limitations PASSED [ 75%]
    tests/test_interpreter.py::test_api_connection_failure_does_not_leak_configuration PASSED [100%]

    ============================== 4 passed in 0.63s ==============================
## 结论

4 个离线测试全部通过，运行过程不访问真实 DeepSeek API，也不需要真实 API Key。

其中“证据不足”测试同时验证：正常的不足证据响应会说明限制；若模型把摘要中存在的数值错误关联到其他类别或指标，程序会拒绝该结果。