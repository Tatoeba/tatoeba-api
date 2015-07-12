#!/bin/bash

pkgver=1.2.18
mkdir -p $VIRTUAL_ENV/src && cd $VIRTUAL_ENV/src

wget -c http://oligarchy.co.uk/xapian/$pkgver/xapian-bindings-$pkgver.tar.xz && tar xf xapian-bindings-$pkgver.tar.xz

cd $VIRTUAL_ENV/src/xapian-bindings-$pkgver
./configure --prefix=$VIRTUAL_ENV --with-python && make && make install
