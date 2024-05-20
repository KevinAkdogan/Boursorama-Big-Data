FROM ubuntu:latest
MAINTAINER Olivier Ricou <olivier@ricou.eu.org>

# If you have a web spider getting data, then you can run 
# that analyzer every nigth (therefore cron)

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update                              \
    && apt-get install -y --no-install-recommends   \
       python3 git make python3-pip python3-setuptools cron bzip2 tzdata python3-venv

#RUN pip3 install pip --upgrade
RUN python3 -m venv /home/bourse/.venv

COPY requirements.txt /tmp/
RUN /home/bourse/.venv/bin/python3 -m pip install -r /tmp/requirements.txt
#RUN pip install -r /tmp/requirements.txt

RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
	&& localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8

ENV LANG en_US.
ENV PYTHONPATH "/home/bourse/.local/lib/python3/site-packages/"

RUN cp /usr/share/zoneinfo/Europe/Paris /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

RUN adduser --disabled-password --gecos "" bourse
RUN chmod 755 /home/bourse

USER bourse
WORKDIR /home/bourse
ADD apps.tgz .
# COPY cronfile /tmp/
# RUN crontab /tmp/cronfile

# USER root
# RUN touch /var/log/cron.log
# CMD service cron start  && \
#     tail -f /var/log/cron.log

CMD /home/bourse/.venv/bin/python3 analyzer.py
