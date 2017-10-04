FROM php:5.6-apache
# docker build -t rankfinder .
# docker run -d -p 8081:80 --name rankfinder rankfinder
# docker exec -it rankfinder bash
RUN apt-get -y update \
 && apt-get -y install git emacs

RUN mkdir /opt/tools && chmod -R 755 /opt/tools
ADD https://api.github.com/repos/jesusjda/pyRankFinder/git/refs/heads/master version1.json
ENV PYRANKFINDER_HOME /opt/tools/pyRankFinder
RUN git clone https://github.com/jesusjda/pyRankFinder /opt/tools/pyRankFinder
RUN cd /opt/tools/pyRankFinder && ./docker.sh -p=2 -p=3
ADD https://api.github.com/repos/jesusjda/easyinterface-config/git/refs/heads/master version2.json
RUN git clone https://github.com/jesusjda/easyinterface-config.git /opt/tools/easyinterface-config \
 && cd /opt/tools/easyinterface-config && ./install.sh --ei-home=/var/www/easyinterface --install-ei

