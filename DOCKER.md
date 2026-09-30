# Run IT2 with Docker

Docker packages the same Python library, paper files and Streamlit checker. It does not require Anaconda on the machine running the container. Docker Desktop must be running with Linux containers on Windows.

## Start locally

From the repository root:

```bash
docker compose up -d --build --remove-orphans
docker compose ps
docker compose logs checker
```

On Windows you can also run `run_docker_windows.bat`. Open **http://127.0.0.1:8501**. Docker Desktop shows one application container, `it2-checker`, with clickable port 8501. Stop any other app using host port 8501 first.

The container runs the downloader before starting Streamlit; existing models are reused on later starts. IFC models are stored in a named Docker volume and are excluded from the image build and Git. Existing models are reused according to the original download script. Paper results and figures stay inside the read-only application image.

The app runs as a non-root user, with a writable temporary directory and a separate reproduction volume. The default demo configuration disables expensive experiment-launch buttons; provenance, figures, model uploads and the topology/identity checker remain available. Uploads are limited to 100 MB per file. The public demo is not a confidential data-sharing service: users should only upload models they are permitted to share with its operator.

## Reproduce inside Docker

Run from your own terminal:

```bash
docker compose exec checker python scripts/reproduce_study.py --mode saved-features
```

Outputs go to the separate reproduction volume; the paper snapshot is preserved. For locally controlled use you can set `IT2_PUBLIC_DEMO` to `0` in Compose and recreate the checker to enable the app's experiment buttons. Default resource limits are two CPU cores and 2 GB RAM; geometry extraction on large models may need more resources.

## Temporary public demo

```bash
docker compose logs checker
```

With `IT2_SHARE: "1"`, the official Cloudflare connector runs inside the same container and prints a generated HTTPS `trycloudflare.com` URL. The link changes when a new tunnel is created and works only while the PC, Docker and tunnel remain running. This is a development/demo link, not permanent hosting. No inbound router port needs to be opened; the connector proxies to Streamlit inside the same container.

To disable sharing, set `IT2_SHARE` to `0` in Compose and run `docker compose up -d`. Recreating the container generates a new demo URL when sharing is enabled again.

## Stop or update

```bash
docker compose down
git pull
docker compose up -d --build --remove-orphans
```

`down` retains the named volumes. Avoid `down -v` unless you intend to delete the downloaded models and reproduction outputs.

## Permanent hosting

Use the Dockerfile on a container host that supports persistent volumes, outbound downloads, HTTP/WebSocket proxying and HTTPS. A stable public hostname and an always-on host are required; running Docker on a laptop alone does not provide permanent hosting. Streamlit Community Cloud is another deployment option and uses the Python repository rather than this Docker Compose setup.

Dependencies retain the repository's declared version ranges. The reproduction report records the installed versions; the image is not a full dependency lockfile.
