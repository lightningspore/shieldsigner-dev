FROM python:3.13.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.7 /uv /usr/local/bin/uv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DEBUG=0 HOME=/tmp PATH="/app/.venv/bin:$PATH"
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY siteconfig siteconfig
COPY knowledge knowledge
COPY templates templates
COPY static static
COPY content content
COPY public public
COPY manage.py ./
RUN .venv/bin/python manage.py collectstatic --noinput && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin shieldsigner
USER 10001:10001
EXPOSE 8000
CMD ["gunicorn", "siteconfig.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "2", "--access-logfile", "-", "--error-logfile", "-"]
