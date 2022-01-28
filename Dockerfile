FROM archlinux
RUN pacman --noconfirm -Syyu && \
    pacman --noconfirm -S python python-aiohttp pyalpm python-pip && \
    pacman --noconfirm -Sc && \
    python -m pip install betterlogging~=0.0.9
COPY * /app/
WORKDIR /app
CMD ["python", "main.py", "--verbose"]
