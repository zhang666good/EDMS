from pymilvus import MilvusClient, DataType
import traceback
import sys


def m():
    print("开始执行...")

    try:
        print("正在连接 Milvus 服务器...")
        client = MilvusClient(
            uri="http://server.wlove.top:19530",
            token="zhang666:Python666good@",
            db_name="qyjc",
        )

        print("成功连接到 Milvus 服务器")

        print("正在创建 schema...")
        schema = MilvusClient.create_schema(
            auto_id=False,
            enable_dynamic_field=True,
        )

        # 3.2. Add fields to schema
        schema.add_field(field_name="my_id", datatype=DataType.INT64, is_primary=True)
        schema.add_field(field_name="my_vector", datatype=DataType.FLOAT_VECTOR, dim=5)
        schema.add_field(field_name="my_varchar", datatype=DataType.VARCHAR, max_length=512)

        print("正在准备索引参数...")
        index_params = client.prepare_index_params()

        # 3.4. Add indexes
        index_params.add_index(
            field_name="my_id",
            index_type="AUTOINDEX"
        )

        index_params.add_index(
            field_name="my_vector",
            index_type="AUTOINDEX",
            metric_type="COSINE"
        )

        print("正在创建集合...")
        # 先检查集合是否已存在，如果存在则删除
        if client.has_collection(collection_name="customized_setup_1"):
            print("集合已存在，正在删除...")
            client.drop_collection(collection_name="customized_setup_1")

        # 3.5. Create a collection with the index loaded simultaneously
        client.create_collection(
            collection_name="customized_setup_1",
            schema=schema,
            index_params=index_params
        )

        print("成功创建集合")

        print("正在获取加载状态...")
        res = client.get_load_state(
            collection_name="customized_setup_1"
        )

        print(f"加载状态: {res}")

        print("程序执行完成")

    except Exception as e:
        print(f"发生错误: {e}")
        traceback.print_exc()


if __name__ == '__main__':
    print("启动程序...")
    m()
    print("程序结束")
