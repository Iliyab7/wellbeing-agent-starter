FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 WELLBEING_MVP_HOME=/state WELLBEING_BIND=0.0.0.0 PORT=8787
WORKDIR /app
COPY requirements-mvp.txt /app/requirements-mvp.txt
RUN pip install --no-cache-dir -r /app/requirements-mvp.txt && groupadd --gid 10001 wellbeing && useradd --uid 10001 --gid wellbeing --no-create-home wellbeing && mkdir /state && chown wellbeing:wellbeing /state && chmod 700 /state
COPY wellbeing /app/wellbeing
COPY scripts /app/scripts
USER 10001:10001
EXPOSE 8787
CMD ["python", "scripts/container_start.py"]
