# File Transfer based on curl <-> CDN

(1) Ordinary `curl` Flow

```
curl --interface uesimtun0 -o lecture12_SupML_buluc24.pdf https://pub-cf250a7dff0b40dea71497e179a340b7.r2.dev/lecture12_SupML_buluc24.pdf
```

(2) Auto-Continue Mode

```
curl --interface uesimtun0 -C - -o lecture12_SupML_buluc24.pdf https://pub-cf250a7dff0b40dea71497e179a340b7.r2.dev/lecture12_SupML_buluc24.pdf
```

(3) Debug

```
curl -v --interface uesimtun0 -C - -o lecture12_SupML_buluc24.pdf https://pub-cf250a7dff0b40dea71497e179a340b7.r2.dev/lecture12_SupML_buluc24.pdf
```

**How to Conduct**

```
./uersat.py start open5gs1
```

```
curl --interface uesimtun0 …
```

```
./uersat.py switch open5gs2
```

```
CTRL+C (curl)
```

```
curl --interface uesimtun0 …
```

