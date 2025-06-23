ARG PYTHON_VERSION=3.13.4
ARG UV_VERSION=0.7.11

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
FROM python:${PYTHON_VERSION}-bookworm AS python
ARG UV_PROJECT_ENVIRONMENT=/opt/python
ENV PATH=${UV_PROJECT_ENVIRONMENT}/bin:$PATH

FROM python AS builder
WORKDIR /source
COPY --from=uv /uv /uvx /usr/local/bin/
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync \
        --all-extras \
        --all-groups \
        --locked \
        --no-install-project

FROM python
RUN --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update \
 && apt-get install -y --no-install-recommends \
    bash-completion \
    gh \
    jq \
    less \
    locales \
    man \
    nano \
    openssh-client \
    rsync \
    screen \
    vim \
    zsh \
 && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
 && locale-gen en_US.UTF-8

ARG DOCKER_VERSION=28.1.1
ARG DOCKER_COMPOSE_VERSION=2.36.0
ARG DIND_FEATURE_VERSION=87fd9a35c50496f889ce309c284b9cffd3061920
ARG DOCKER_GID=999
ENV DOCKER_BUILDKIT=1
RUN --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update \
 && curl -fsSL https://raw.githubusercontent.com/devcontainers/features/${DIND_FEATURE_VERSION}/src/docker-in-docker/install.sh \
    | env VERSION=${DOCKER_VERSION} \
    DOCKERDASHCOMPOSEVERSION=${DOCKER_COMPOSE_VERSION} \
    bash \
 && apt-get update # install script clears apt list cache \
 && groupmod -g ${DOCKER_GID} docker

COPY --from=uv /uv /uvx /usr/local/bin/

RUN echo 'eval "$(uv generate-shell-completion bash)"' >> /etc/bash_completion.d/uv \
 && docker completion bash > /etc/bash_completion.d/docker

ARG APP_USER=metr
ARG APP_DIR=/home/${APP_USER}/app
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN groupadd -g ${GROUP_ID} ${APP_USER} \
 && useradd ${APP_USER} \
    -u ${USER_ID} \
    -g ${APP_USER} \
    -G docker \
    -m \
    -s /bin/bash \
 && mkdir -p ${APP_DIR} /home/${APP_USER}/.cache/inspect_ai \
 && chown -R ${USER_ID}:${GROUP_ID} ${APP_DIR} /home/${APP_USER}

COPY --from=builder --chown=${USER_ID}:${GROUP_ID} ${UV_PROJECT_ENVIRONMENT} ${UV_PROJECT_ENVIRONMENT}
WORKDIR ${APP_DIR}
ENTRYPOINT ["/usr/local/share/docker-init.sh"]
CMD ["sleep", "infinity"]
