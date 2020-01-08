FROM python:3

COPY ./* /v2ray_agent
RUN cd /v2ray_agent && pip3 install -r requirements.txt
WORKDIR /v2ray_agent

CMD [ "python3", "v2ray_agent.py" ]
