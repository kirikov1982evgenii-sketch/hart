FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || true
COPY . .
RUN mkdir -p data/receipts
ENV BIND_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1
EXPOSE 8765 8766
CMD sh -c "python scripts/gen_config.py 2>/dev/null || true; python payment_server.py & python telegram_bot.py & exec python site_server.py"
