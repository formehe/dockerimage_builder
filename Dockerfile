FROM wemakeservices/wemake-dind:24.0.0

RUN apk --no-cache add tini

WORKDIR /home/app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x start.sh

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["./start.sh"]