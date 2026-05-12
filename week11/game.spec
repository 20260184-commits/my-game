a = Analysis( 
    ['game.py'],
    datas = [
        ('assets', 'assets'),
        ('fonts' , 'fonts'),
        ('sounds', 'sounds'),
    ],
    hiddenimports= [],
)