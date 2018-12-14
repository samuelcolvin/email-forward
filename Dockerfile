# ===============================================
# pre-built python dependency stage
FROM email-forward-base as base

# ===============================================
# final image
FROM python:3.7-alpine3.8

ENV PYTHONUNBUFFERED 1
ENV APP_ON_DOCKER 1
WORKDIR /home/root
RUN adduser -D runuser
USER runuser

COPY --from=base /lib/* /lib/
COPY --from=base /usr/lib/* /usr/lib/
COPY --from=base /usr/local/lib/python3.7/site-packages /usr/local/lib/python3.7/site-packages

ADD ./run.py /home/root

ARG COMMIT
ENV COMMIT $COMMIT
ARG BUILD_TIME
ENV BUILD_TIME $BUILD_TIME

CMD ["./run.py"]
