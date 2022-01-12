FROM archlinux
RUN pacman --noconfirm -Syyu && \
    pacman --noconfirm -S python pyalpm python-aiohttp && \
    pacman --noconfirm -Sc
COPY *.py /app/
WORKDIR /app
RUN mkdir db
CMD ["python", "main.py"]