FROM archlinux
RUN pacman --noconfirm -Syyu && \
    pacman --noconfirm -S python aiohttp pyalpm python-pip && \
    pacman --noconfirm -Sc
COPY * /app/
WORKDIR /app
RUN python -m pip install betterlogging~=0.0.9

CMD ["python", "main.py", "--verbose"]