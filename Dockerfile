FROM php:5.6-apache
# docker build -t rankfinder .
# docker run -d -p 8081:80 --name rankfinder rankfinder
# docker exec -it rankfinder bash
RUN apt-get -y update \
 && apt-get -y install git emacs

RUN mkdir /opt/tools && chmod -R 755 /opt/tools
ADD https://api.github.com/repos/jesusjda/pyRankFinder/git/refs/heads/master version.json
RUN git clone https://github.com/jesusjda/pyRankFinder /opt/tools/pyRankFinder
RUN cd /opt/tools/pyRankFinder && ./docker.sh -p=2 -p=3
# RUN git clone https://github.com/abstools/absexamples.git /var/www/absexamples \
#  && chmod -R 755 /var/www/absexamples \
RUN git clone https://github.com/jesusjda/easyinterface-config.git /opt/tools/easyinterface-config \
 && cd /opt/tools/easyinterface-config && ./install.sh --ei-home=/var/www/easyinterface --install-ei
ENV PYRANKFINDER_HOME /opt/tools/pyRankFinder
