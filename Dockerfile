FROM php:5.6-apache
# docker build -t rankfinder .
# docker run -d -p 8081:80 --name rankfinder rankfinder
# docker exec -it rankfinder bash
RUN apt-get -y update \
 && apt-get -y install git emacs
ADD https://api.github.com/repos/jesusjda/pyRankFinder/git/refs/heads/master version.json
RUN git clone https://github.com/jesusjda/pyRankFinder
RUN cd pyRankFinder && ./docker.sh -p=2