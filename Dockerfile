FROM python:3.11

USER root 
ARG APP_PATH=/home/admin

RUN mkdir ${APP_PATH}
COPY db.py ${APP_PATH}
COPY endpoint.py ${APP_PATH}
COPY swagger.json ${APP_PATH}
COPY requirements.txt ${APP_PATH}
RUN pip install -r  ${APP_PATH}/requirements.txt

# create admin user
ARG uid=1000
ARG gid=1000
RUN groupadd -r -f -g ${gid} admin && useradd -o -r -l -u ${uid} -g ${gid} -ms /bin/bash admin
RUN usermod -aG sudo admin
RUN echo 'admin:Password7' | chpasswd
RUN chown -R admin:admin ${APP_PATH}
USER admin

WORKDIR /home/admin
COPY swagger.yml ${APP_PATH}
ENTRYPOINT python3 endpoint.py --port ${PORT} --postgres_host ${P_HOST} --postgres_port ${P_PORT} 
