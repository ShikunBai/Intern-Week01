# 离线测试结果

## 执行命令

```bash
python -m pytest tests/ -v
```
## 最终结果
4 passed

## 四个离线测试
1.test_summary_contains_correct_group_metrics
  验证 pandas 摘要的总行数、缺失数、Govt_job 样本数和平均血糖水平。

2.test_normal_structured_response_parses_without_real_api
  使用假客户端模拟正常 JSON 响应，验证其可解析为 AnalysisResult，且请求使用 JSON Output 与非流式模式。

3.test_insufficient_evidence_response_states_limitations
  使用假客户端模拟证据不足场景，验证结论与限制明确说明证据不足，且证据值可在摘要中找到。

4.test_api_connection_failure_does_not_leak_configuration
  模拟 API 连接失败，验证程序返回受控错误，且错误输出不泄露模拟密钥。

所有测试均不访问真实 DeepSeek API，也不需要真实 API Key。
