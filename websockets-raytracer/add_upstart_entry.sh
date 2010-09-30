if [ ! "`whoami`" = "root" ]; then
  echo "Not running as root"
  exit
fi

echo -e "start on startup \n\
exec python `pwd`/server.py \n\
respawn \n\
respawn limit 10 90" > /etc/init/raytracer.conf

echo "Wrote /etc/init/raytracer.conf"

