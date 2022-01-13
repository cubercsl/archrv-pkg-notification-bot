FROM archlinux
RUN pacman --noconfirm -Syyu && \
    pacman --noconfirm -S python pyalpm python-aiohttp && \
    pacman --noconfirm -Sc
COPY * /app/
WORKDIR /app

CMD ["python", "main.py", "--verbose"]