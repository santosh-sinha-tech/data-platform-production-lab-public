FROM python:3.11.14-slim@sha256:c8271b1f627d0068857dce5b53e14a9558603b527e46f1f901722f935b786a39
WORKDIR /lab
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH=/lab/src
EXPOSE 8000
CMD ["uvicorn","agent_lab.app:app","--host","0.0.0.0","--no-access-log"]
