rm -rf c1 c2 s
mkdir c1 c2 s
cp -r test_blackjay c1/.blackjay
cp -r test_blackjay c2/.blackjay
python server.py s
