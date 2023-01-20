from app import app
import uvicorn
from filewatcher import start_monitoring_files
if __name__ == "__main__":
    start_monitoring_files()
    uvicorn.run(app, host="127.0.0.1", port=8000)
