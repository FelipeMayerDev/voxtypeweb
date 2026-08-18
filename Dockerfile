# Fedora 44 required: host glibc is 2.43, the bind-mounted voxtype binary
# needs a matching-or-newer glibc than what Debian/Ubuntu base images ship.
FROM fedora:44

# python + runtime libs the bind-mounted voxtype binary links against
# (libasound.so.2 = alsa-lib, libstdc++.so.6 = libstdc++); glibc/libgcc are in the base.
RUN dnf install -y python3 python3-pip alsa-lib libstdc++ && dnf clean all

RUN useradd --uid 1000 --create-home appuser

WORKDIR /app

COPY pyproject.toml ./
COPY app/ ./app/
COPY templates/ ./templates/
COPY static/ ./static/

RUN pip install --no-cache-dir .

USER 1000

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
