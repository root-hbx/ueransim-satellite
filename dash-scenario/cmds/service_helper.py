import logging
import subprocess


def start_wondershaper_service() -> None:
    """Start the wondershaper service"""
    try:
        subprocess.run(["sudo", "systemctl", "start", "wondershaper.service"], check=True)
        logging.info("Wondershaper service started")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error starting wondershaper service: {e}")


def stop_wondershaper_service() -> None:
    """Stop the wondershaper service"""
    try:
        subprocess.run(["sudo", "systemctl", "stop", "wondershaper.service"], check=True)
        logging.info("Wondershaper service stopped")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error stopping wondershaper service: {e}")


