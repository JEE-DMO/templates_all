Le pod driver est supprimé par Airflow après l'échec. Il faut donc soit lancer un pod de debug dans le même namespace avec la même image, le même service account et les mêmes labels (pour hériter des mêmes network policies), soit mettre temporairement un `sleep` dans un pod de test.

```bash
kubectl -n <namespace> run dbg --rm -it --image=<image_spark_utilisee> --command -- bash
# ou, si le pod existe encore :
kubectl -n <namespace> exec -it <pod> -- bash
```

Les outils (`curl`, `nc`, `nslookup`) peuvent manquer dans l'image Spark. Chaque test a donc une alternative en bash ou Python.

**1. Variables d'environnement et proxy**
```bash
env | grep -i -E 'proxy|socks|no_proxy|aws|s3'
cat /etc/resolv.conf
```
La stack trace passe par `SocksSocketImpl`, donc vérifie si un proxy SOCKS est défini (`-DsocksProxyHost`, `JAVA_TOOL_OPTIONS`, `SPARK_*_OPTS`).

**2. Résolution DNS**
```bash
nslookup bu002i013655.s3.direct.eu-fr2.cloud-object-storage.appdomain.cloud
getent hosts bu002i013655.s3.direct.eu-fr2.cloud-object-storage.appdomain.cloud
```
L'IP attendue est `55.72.188.16`.

**3. Connectivité TCP (le test clé)**
```bash
nc -zv -w 10 bu002i013655.s3.direct.eu-fr2.cloud-object-storage.appdomain.cloud 4289
# sans nc :
timeout 10 bash -c '</dev/tcp/55.72.188.16/4289' && echo OK || echo KO
# ou en Python :
python3 -c "import socket; s=socket.create_connection(('55.72.188.16',4289),10); print('OK')"
```
Un timeout ici confirme un blocage réseau. Un `Connection refused` signifierait que l'hôte répond mais que rien n'écoute sur le port.

**4. Test HTTPS et TLS**
```bash
curl -v --connect-timeout 10 https://bu002i013655.s3.direct.eu-fr2.cloud-object-storage.appdomain.cloud:4289
openssl s_client -connect 55.72.188.16:4289 -servername bu002i013655.s3.direct.eu-fr2.cloud-object-storage.appdomain.cloud </dev/null
```
Une réponse 403 ou `AccessDenied` est bon signe, car le réseau passe. Un timeout veut dire que ça bloque avant.

**5. Chemin réseau**
```bash
traceroute -n -T -p 4289 55.72.188.16
tracepath 55.72.188.16
ip route
```

**6. Comparaison avec d'autres endpoints**
```bash
curl -v --connect-timeout 10 https://s3.direct.eu-fr2.cloud-object-storage.appdomain.cloud:4289
nc -zv -w 10 <autre_endpoint_COS_ou_service_interne> <port>
```
Cela permet de savoir si tout l'egress est coupé ou seulement ce endpoint.

**7. Configuration S3A effective de Spark**
```bash
env | grep -i spark
grep -ri -E 's3a|iceberg' $SPARK_HOME/conf/ 2>/dev/null
```
Vérifie surtout `spark.hadoop.fs.s3a.endpoint`, `fs.s3a.path.style.access`, `fs.s3a.connection.ssl.enabled` et `fs.s3a.connection.establish.timeout`.

**8. Test applicatif depuis PySpark** (reproduit exactement l'erreur)
```bash
pyspark  # puis :
spark.read.format("iceberg").load("<db_depositi>.<tb_ndg_esclusi>").limit(1).show()
```
Ou directement avec Hadoop :
```python
sc._jvm.org.apache.hadoop.fs.FileSystem.get(
  sc._jvm.java.net.URI("s3a://bu002i013655/"), sc._jsc.hadoopConfiguration()
).exists(sc._jvm.org.apache.hadoop.fs.Path("s3a://bu002i013655/depositi_titoli/depositi_ndg_da_escludere/metadata/"))
```

**9. Côté Kubernetes (hors pod)**
```bash
kubectl -n <namespace> get networkpolicy -o yaml
kubectl -n <namespace> describe pod <pod> | grep -i -E 'node|ip|label|serviceaccount'
kubectl get events -n <namespace> --sort-by=.lastTimestamp | tail -30
```
Compare aussi avec un autre DAG qui lit le même bucket, pour voir s'il tourne sur un autre node ou namespace.

**Comment interpréter les résultats**
- Le DNS échoue : problème de résolution (CoreDNS, `resolv.conf`).
- Le DNS passe mais le TCP time out : firewall, network policy ou route (cas le plus probable d'après les logs).
- Le TCP passe mais le test applicatif échoue : problème de proxy, de config S3A ou de credentials.
- Tout passe maintenant : le problème était transitoire, à rapprocher de l'incident INC16755676 et à relancer le task.

Si tu me colles les sorties des tests 2 à 4, je peux t'aider à les interpréter.
