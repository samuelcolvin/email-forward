# ===============================================
# pre-built python dependency stage
FROM email-forward-base as base

# ===============================================
# final image
FROM python:3.7-alpine3.8

ENV PYTHONUNBUFFERED 1
WORKDIR /home/root
USER root

COPY --from=base /lib/* /lib/
COPY --from=base /usr/lib/* /usr/lib/
COPY --from=base /usr/local/lib/python3.7/site-packages /usr/local/lib/python3.7/site-packages

ADD ./run.py /home/root

CMD ["./run.py"]
