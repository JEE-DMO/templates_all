**Synthèse (uniquement ce que montrent les captures)**

- **Run du 13/11 :** les appels API de la page 0 et de la page 1 sont lancés par le thread `main` du driver. La page 0 répond en 3 s (code 200). La page 1 est lancée à 23:01:12 et **aucun `Response code` ne suit**.
- **Même motif le 03/11.** Je l'avais pris pour un run sain, mais il est identique : page 1 lancée à 23:01:26, jamais de réponse, dernier log à 23:06:21. Le blocage se reproduit donc.
- **L'executor est sain mais inactif.** Il s'enregistre, récupère le jar et ne reçoit aucune tâche. Ses logs s'arrêtent à 23:01:23, et la Spark UI est vide parce qu'aucun job n'a été soumis.
- **`No executor found for ...`** tombe à ~5 min pile après le démarrage, sur les deux runs, avec un port différent de l'executor enregistré. C'est une connexion secondaire qui se ferme, pas un executor perdu. Ce n'est pas la cause.
- **Côté Airflow,** la stacktrace montre le worker bloqué sur la lecture du flux de logs du pod, donc le pod driver tournait encore. À 11:19:09 (soit 12 h plus tard), la tâche est passée en failed de l'extérieur, d'où SIGTERM puis le 409 au cleanup, qui n'est qu'un effet secondaire.

**Hypothèse unique**

Le driver reste bloqué indéfiniment sur la requête HTTP de la page 1, sans read timeout dans `Logic`. La réponse n'arrive jamais, ou la connexion est coupée silencieusement par le réseau, et le thread `main` attend sans fin. Spark et l'executor ne sont pas en cause : le driver n'a jamais délégué quoi que ce soit.

**Pour la confirmer**

- Tes captures k9s montrent encore les pods du 03/11 le 14/11 au soir. Si ce driver est toujours là, il est `Running` depuis 11 jours (la rétention ne touche pas les pods Running). Dans ce cas, fais un `jcmd 1 Thread.print` dessus : `main` devrait être sur un `socketRead`. Un `ss -tnp` montrera la connexion vers `api-restricted-pfc`.
- Ajoute des timeouts connect et read avec retry dans `Logic`, et un `execution_timeout` sur la tâche Airflow.
