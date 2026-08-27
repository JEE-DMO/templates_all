Côté Oracle, les vérifications les plus utiles sont celles-ci, idéalement **pendant qu’une task Airflow est bloquée** :

1. **Identifier la session Oracle correspondant à la task**

   ```sql
   SELECT sid, serial#, username, status, machine, program, module,
          sql_id, event, wait_class, seconds_in_wait, blocking_session
   FROM v$session
   WHERE username = '<USER>';
   ```

2. **Vérifier si la session est en attente**
   Regarder surtout :

   * `EVENT`
   * `WAIT_CLASS`
   * `SECONDS_IN_WAIT`
   * `STATE`

   Exemples suspects :

   * `enq: TX - row lock contention`
   * `enq: TM - contention`
   * I/O waits
   * `SQL*Net message ...`

3. **Identifier une éventuelle session bloquante**

   ```sql
   SELECT sid, serial#, username, sql_id, event,
          blocking_session, seconds_in_wait
   FROM v$session
   WHERE blocking_session IS NOT NULL;
   ```

4. **Contrôler les verrous actifs**

   ```sql
   SELECT *
   FROM v$lock
   WHERE block = 1 OR request > 0;
   ```

   Et si disponible, regarder aussi `DBA_BLOCKERS` / `DBA_WAITERS`.

5. **Identifier le SQL réellement exécuté**
   À partir du `SQL_ID` :

   ```sql
   SELECT sql_id, sql_text
   FROM v$sql
   WHERE sql_id = '<SQL_ID>';
   ```

6. **Vérifier le plan d’exécution**

   ```sql
   SELECT *
   FROM TABLE(DBMS_XPLAN.DISPLAY_CURSOR('<SQL_ID>', NULL, 'ALLSTATS LAST'));
   ```

   Comparer avec les runs rapides d’avant le 06/08.

7. **Vérifier si le plan SQL a changé depuis le 06/08**
   Chercher :

   * nouveau plan hash value
   * changement d’index
   * statistiques mises à jour
   * changement de cardinalité
   * full scan apparu récemment

8. **Contrôler les sessions longues ou orphelines**

   ```sql
   SELECT sid, serial#, username, status, logon_time,
          last_call_et, sql_id, event
   FROM v$session
   WHERE username = '<USER>'
   ORDER BY logon_time;
   ```

   Chercher des sessions ouvertes depuis plusieurs heures.

9. **Vérifier les transactions non commit**

   ```sql
   SELECT s.sid, s.serial#, t.start_time, t.used_ublk, t.used_urec
   FROM v$transaction t
   JOIN v$session s ON s.taddr = t.addr;
   ```

10. **Analyser AWR / ASH**
    Comparer :

    * avant le 06/08
    * après le 06/08
    * pendant un run bloqué

    À regarder :

    * top wait events
    * blocking sessions
    * elapsed time du SQL
    * CPU
    * reads
    * execution count
    * execution plan

11. **Vérifier la concurrence sur les mêmes tables**
    Confirmer si plusieurs runs exécutent simultanément les mêmes :

    * `MERGE`
    * procédures
    * tables cibles
    * partitions

12. **Vérifier les changements Oracle autour du 06/08**

    * déploiement de procédure
    * changement d’index
    * stats recalculées
    * patch DB
    * changement de configuration
    * resource manager
    * modification de service Oracle

13. **Vérifier la consommation ressources DB**
    Pendant le blocage :

    * CPU
    * I/O
    * sessions actives
    * sessions en attente
    * nombre de process
    * saturation PGA/SGA
    * limites `sessions/processes`

14. **Vérifier si la connexion est coupée après plusieurs heures**
    Pour le `DPY-4011`, contrôler :

    * DB timeout
    * firewall / load balancer timeout
    * idle timeout
    * SQLNET settings
    * kill de session côté DBA

Le point principal à demander à l’équipe Oracle est simple :

> **When an Airflow task is stuck, please identify the corresponding Oracle session and determine exactly what it is waiting for, whether it is blocked by another session, and which SQL_ID / execution plan is involved.**

C’est cette information qui permettra de distinguer rapidement entre **lock, contention, plan SQL dégradé, saturation DB ou problème réseau**.
