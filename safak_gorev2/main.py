"""Kaldırılan quad uçuş girişi; donanım açmadan hata verir."""
def main():
    print('Eski quad seçeneği kaldırıldı. Ana görev: python -m safak_gorev2.competition.main --task ana; '
          'hızlı görev: python -m safak_gorev2.competition.main --task hizli. Varsayılan yalnız gözlem.')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
