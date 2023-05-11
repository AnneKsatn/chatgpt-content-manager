import uvicorn

if __name__ == '__main__':
  uvicorn.run("app.main:app",
                host="95.179.162.88",
                port=8432,
                reload=True,
                ssl_keyfile="./key.pem",
                ssl_certfile="./cert.pem"
                )
