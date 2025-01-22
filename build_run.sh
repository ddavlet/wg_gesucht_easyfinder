docker build app/tg_bot/ -t tg_bot && docker run --env-file app/tg_bot/.env tg_bot

docker build app/parser/ -t parser && docker run --env-file app/parser/.env parser
