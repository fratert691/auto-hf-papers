# auto-hf-papers

每天抓取 [Hugging Face Daily Papers](https://huggingface.co/papers)，筛选出真正值得看的论文，并在北京时间早上 9 点自动发送邮件。

当前实现是单一路径：

- Python 负责抓取、筛选、生成 Markdown digest
- Node.js 负责通过 Resend 发邮件
- cron 负责每天定时执行

## 筛选规则

论文满足以下任一条件就会被收录：

- `Hugging Face upvotes > 20`
- `GitHub stars > 100`

生成结果写入：

- `outputs/YYYY-MM-DD.md`

每篇论文包含：

- 标题
- 入选原因
- Hugging Face upvotes
- GitHub stars
- 中文简介
- Hugging Face / GitHub / project page 链接

## 工作原理

1. 请求 `https://huggingface.co/papers/date/YYYY-MM-DD`
2. 解析页面里嵌入的 `DailyPapers` JSON
3. 读取 `upvotes`、`summary`、`ai_summary`、`githubRepo`、`projectPage`
4. 对存在 GitHub 仓库的论文调用 GitHub API 查询 star 数
5. 按阈值过滤
6. 生成 Markdown digest
7. 通过 Resend 发邮件

第一版不抓 PDF，也不解析 arXiv 全文。

## 环境要求

- `python3` 3.9+
- `node` 18+

本机当前实际路径是：

- Python: `/usr/bin/python3`
- Node: `/opt/homebrew/bin/node`

## 本地安装

```bash
cd /Users/hetong.31/code/auto-hf-papers
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## 手动生成 digest

生成今天的 digest：

```bash
python -m app.run
```

生成指定日期的 digest：

```bash
python -m app.run --date 2026-03-25
```

覆盖默认阈值：

```bash
python -m app.run --upvotes 10 --stars 50
```

输出到其他目录：

```bash
python -m app.run --output-dir tmp/digests
```

可选：设置 `GITHUB_TOKEN` 提高 GitHub API 配额：

```bash
export GITHUB_TOKEN=ghp_xxx
python -m app.run --date 2026-03-25
```

说明：

- `GITHUB_TOKEN` 不是必须
- 没有 token 也能运行
- 但在 GitHub API 限流时，star 查询可能失败

## 邮件配置

本地配置目录：

- `~/.hf-papers/config.json`
- `~/.hf-papers/.env`

`~/.hf-papers/config.json` 示例：

```json
{
  "onboardingComplete": true,
  "language": "zh",
  "upvoteThreshold": 20,
  "githubStarsThreshold": 100,
  "deliveryMethod": "email",
  "timezone": "Asia/Shanghai",
  "schedule": {
    "frequency": "daily",
    "time": "09:00"
  },
  "email": {
    "address": "your_email@example.com"
  }
}
```

`~/.hf-papers/.env` 示例：

```bash
RESEND_API_KEY=re_xxx
```

要求：

- `deliveryMethod` 必须是 `email`
- `email.address` 必须存在
- `RESEND_API_KEY` 必须存在

注意：

- 不要把真实密钥写进仓库
- 不要提交 `~/.hf-papers/.env`

## 手动发送邮件

先生成 digest：

```bash
python -m app.run --date 2026-03-25
```

再发送这一天的邮件：

```bash
node scripts/deliver.js --file=outputs/2026-03-25.md
```

完整手动流程：

```bash
python -m app.run --date 2026-03-25
node scripts/deliver.js --file=outputs/2026-03-25.md
```

## 每天北京时间 09:00 自动发送

自动发送脚本：

- `scripts/send-digest.sh`

脚本逻辑：

1. 用 `Asia/Shanghai` 计算当天日期
2. 运行 Python 生成当天 digest
3. 调用 Node 投递邮件

当前脚本核心命令：

```bash
/usr/bin/python3 -m app.run --date "$RUN_DATE"
/opt/homebrew/bin/node scripts/deliver.js --file=outputs/$RUN_DATE.md
```

当前已安装的 crontab：

```cron
0 9 * * * /Users/hetong.31/code/auto-hf-papers/scripts/send-digest.sh >> /Users/hetong.31/.hf-papers/cron.log 2>&1
```

这表示：

- 每天早上 9 点执行
- 日志写入 `~/.hf-papers/cron.log`

手动重装这条 cron：

```bash
(crontab -l 2>/dev/null | grep -v '/Users/hetong.31/code/auto-hf-papers/scripts/send-digest.sh' ; \
echo '0 9 * * * /Users/hetong.31/code/auto-hf-papers/scripts/send-digest.sh >> /Users/hetong.31/.hf-papers/cron.log 2>&1') | crontab -
```

查看当前 cron：

```bash
crontab -l
```

## 输出格式

生成的 Markdown 包含：

- digest 标题和生成时间
- 当前使用的筛选规则
- 当日论文总数和入选数量
- 每篇论文的单独 section

如果当天没有论文满足条件，也会生成 Markdown 文件，并明确写明“今天没有满足筛选条件的论文”。

## 测试

运行测试：

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## 联调和排错

日志文件：

- `~/.hf-papers/cron.log`

常用命令：

```bash
tail -n 100 ~/.hf-papers/cron.log
cat ~/.hf-papers/config.json
cat ~/.hf-papers/.env
which python3
which node
crontab -l
```

如果你想验证整条 cron 流程，但不真的发邮件：

```bash
DELIVERY_METHOD=stdout /Users/hetong.31/code/auto-hf-papers/scripts/send-digest.sh
```

如果邮件发送失败，重点检查：

- `~/.hf-papers/.env` 里是否有 `RESEND_API_KEY`
- `~/.hf-papers/config.json` 里 `deliveryMethod` 是否为 `email`
- `~/.hf-papers/config.json` 里 `email.address` 是否存在
- `/opt/homebrew/bin/node` 是否存在
- `~/.hf-papers/cron.log` 里是否有报错

## 当前实现的边界

- GitHub star 查询是 best effort，不会因为单个仓库失败而中断整批任务
- GitHub 查询失败时，论文仍然可以凭 Hugging Face upvotes 入选
- 当前比较是严格大于：`upvotes > threshold`、`stars > threshold`
- 当前邮件内容是 Markdown 纯文本直发，不是 HTML 模板邮件
