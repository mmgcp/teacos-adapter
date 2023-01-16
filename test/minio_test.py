from minio import Minio

from tno.aimms_adapter.settings import EnvSettings


def load_from_minio(path):
    minio_client = Minio(
        endpoint=EnvSettings.minio_endpoint(),
        secure=EnvSettings.minio_secure(),
        access_key=EnvSettings.minio_access_key(),
        secret_key=EnvSettings.minio_secret_key()
    )

    buckets = minio_client.list_buckets()

    for bucket in buckets:
        print(f"Bucket: {bucket.name}, {bucket.creation_date}")


    bucket = path.split("/")[0]
    rest_of_path = "/".join(path.split("/")[1:])

    response = minio_client.get_object(bucket, rest_of_path)
    if response:
        return response.data
    else:
        return None


if __name__ == '__main__':
    res = load_from_minio("opera-test/NL II3050 with carriers_marginal_cost.esdl")
    print (res.decode('utf-8'))