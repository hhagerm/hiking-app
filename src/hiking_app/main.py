import uvicorn

def main() -> None:
    uvicorn.run(
        app="hiking_app:app",
        host="127.0.0.1",
        port=8000,
        workers=1,
    )

if __name__ == "__main__":
    main()