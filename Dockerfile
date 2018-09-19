FROM php:5.6-apache
# docker build -t rankfinder .
# docker run -d -p 8081:80 --name rankfinder rankfinder
# docker exec -it rankfinder bash
RUN apt-get -y update \
 && apt-get -y install git emacs wget
RUN apt-get -y install make tar curl
RUN apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
xz-utils tk-dev
RUN mkdir /opt/tools && chmod -R 755 /opt/tools
# ADD https://api.github.com/repos/jesusjda/pyRankFinder/git/refs/heads/master version1.json
ENV PYRANKFINDER_HOME /opt/tools/pyRankFinder
# RUN git clone https://github.com/jesusjda/pyRankFinder /opt/tools/pyRankFinder
ADD . $PYRANKFINDER_HOME
RUN $PYRANKFINDER_HOME/installers/install_pe.sh
RUN $PYRANKFINDER_HOME/installers/install_dependencies.sh -p=3
RUN $PYRANKFINDER_HOME/installers/install_modules.sh -p=3

ADD https://api.github.com/repos/jesusjda/easyinterface-config/git/refs/heads/master version2.json
RUN git clone https://github.com/jesusjda/easyinterface-config.git /opt/tools/easyinterface-config && cd /opt/tools/easyinterface-config && ./install.sh --ei-home=/var/www/easyinterface --install-ei --ei-branch=develop
# --ex-home=/var/www/examples --ex-remote=/examples \
RUN a2ensite easyinterface-site
# RUN a2ensite example-site
RUN a2enmod headers
