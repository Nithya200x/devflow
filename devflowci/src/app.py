import os
import socket
from uuid import getnode as get_mac

from flask import Flask, jsonify, render_template


APP_NAME = os.getenv("APP_NAME", "DevFlow")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")


def _format_mac_address(value):
    return "-".join(("%012X" % value)[i : i + 2] for i in range(0, 12, 2))


def _resolve_ip_address():
    pod_ip = os.getenv("POD_IP")
    if pod_ip:
        return pod_ip

    try:
        return socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        return "unavailable"


def get_pod_details():
    return {
        "hostname": os.getenv("HOSTNAME", socket.gethostname()),
        "ip": _resolve_ip_address(),
        "mac": _format_mac_address(get_mac()),
        "node": os.getenv("NODE_NAME", "local"),
        "namespace": os.getenv("POD_NAMESPACE", "local"),
        "version": APP_VERSION,
    }


def create_app():
    app = Flask(__name__)

    @app.route("/")
    def home():
        return render_template(
            "index.html",
            app_name=APP_NAME,
            version=APP_VERSION,
            details=get_pod_details(),
        )

    @app.route("/details")
    def details():
        return render_template(
            "details.html",
            app_name=APP_NAME,
            details=get_pod_details(),
        )

    @app.route("/health")
    def health():
        return jsonify(
            app=APP_NAME,
            status="up",
            version=APP_VERSION,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
