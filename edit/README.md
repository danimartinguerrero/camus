# to seek the unseen — edit de Albert Camus

## v2 · versión corta y dinámica (recomendada)

`camus_edit_v2_es.mp4` / `camus_edit_v2_en.mp4`: 40,5 s, 1080×1920, 30 fps, sin audio.
Solo fotografías y frases (sin fondos decorativos), con clips pequeños sobre las fotos
(Camus hablando, el Nobel, ajedrez, café, lobo en la nieve). 15 frases.
Montado sobre una rejilla de **120 BPM** (un corte cada 0,5 s): elige una canción a ~120 BPM
(o a 60/240) y haz coincidir el primer golpe con el segundo 0.

| Tiempo | Frase |
|---|---|
| 0:00 | me miraban, pero no me veían |
| 0:03 | nadie se da cuenta de que algunas personas gastan una energía tremenda solo para ser normales |
| 0:06 | estoy extrañamente cansado… |
| 0:10 | lo absurdo no libera; ata |
| 0:12 | el hombre es la única criatura que se niega a ser lo que es |
| 0:14 | hay que imaginarse a Sísifo feliz |
| 0:16.5 | no hay amor de vivir sin desesperación de vivir |
| 0:19 | el otoño es una segunda primavera… |
| 0:21.5 | la verdadera generosidad con el futuro… · damn fine coffee |
| 0:24 | vivir hasta las lágrimas |
| 0:25.5 | el mundo es bello, y fuera de él no hay salvación |
| 0:28 | no conozco más que un deber, y es el de amar |
| 0:30.5 | mosaico: …sus colores secretos… |
| 0:33.5 | clímax: …un verano invencible |
| 0:37.5 | nunca fuiste invisible · to seek the unseen |

Re-renderizar: `./tools/render2.sh es` (tiempos en `SEQ` y frases en `TX` dentro de `tools/edit2.py`).

---

## v1 · versión larga

Vertical 1080×1920 · 30 fps · 66 s · **sin audio** (para añadir tu canción).

| Archivo | Contenido |
|---|---|
| `camus_edit_en.mp4` | Versión con frases en inglés |
| `camus_edit_es.mp4` | Versión con frases en español |
| `cover_en.png` / `cover_es.png` | Portada sugerida para TikTok (fotograma del clímax) |

Las fotos se muestran siempre a su resolución original o menor (nunca se amplían) y sin marcas de agua (recortadas).
Todo lo demás (nieve, abetos con niebla, Red Room, Sísifo, hojas, vapor del café, lluvia, polaroids, tira de película, grano) está generado por código, así que se ve nítido a pantalla completa.

## Escaleta (para sincronizar la música)

| Tiempo | Escena | Texto |
|---|---|---|
| 0:00 | Intro, máquina de escribir | *to seek the unseen.* |
| 0:04 | Bosque nevado (abetos, niebla), París | *in the depth of winter…* |
| 0:10 | Collage de tres fotos | *I was looked at, but I wasn't seen.* |
| 0:16 | Red Room (cortinas + suelo de chevrones), retrato enmarcado | *the unreasonable silence of the world.* |
| 0:21 | Sísifo empujando la roca al atardecer | *the struggle itself toward the heights…* |
| 0:27 | Camus sonriendo | *one must imagine Sisyphus happy.* |
| 0:31 | Otoño, hojas cayendo | *autumn is a second spring…* |
| 0:37 | Lluvia en la ventana, vapor saliendo de su café | *real generosity toward the future…* · *damn fine coffee.* |
| 0:43 | Polaroids sobre papel | *…its secret colours…* → *and yet, someone out there sees your secret colours.* |
| 0:50 | Tira de película acelerando | — |
| 0:52 | Clímax: collage que pasa de invierno a verano, la nieve sube como brasas | *…an invincible summer.* |
| 0:60 | Retrato a lápiz | *you were never unseen.* |

Momentos fuertes para un *drop*: 0:52.6 (destello blanco → clímax) y 0:55–0:57 (el color se calienta).

## Re-renderizar (p. ej. para cambiar tiempos o frases)

Requiere Python 3 con `numpy` y `pillow`, y `ffmpeg`.

```bash
./tools/render.sh es
```

Las frases están en el diccionario `TX` y los tiempos de cada escena en `TL`, ambos dentro de `tools/edit.py`.
