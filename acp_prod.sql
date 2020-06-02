PGDMP     0    "                x           acp_prod    12.2    12.2                0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                      false                       0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                      false                       0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                      false                       1262    16433    acp_prod    DATABASE     �   CREATE DATABASE acp_prod WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'English_United States.1252' LC_CTYPE = 'English_United States.1252';
    DROP DATABASE acp_prod;
                postgres    false                        3079    16665 	   adminpack 	   EXTENSION     A   CREATE EXTENSION IF NOT EXISTS adminpack WITH SCHEMA pg_catalog;
    DROP EXTENSION adminpack;
                   false                       0    0    EXTENSION adminpack    COMMENT     M   COMMENT ON EXTENSION adminpack IS 'administrative functions for PostgreSQL';
                        false    1            �            1259    16674    bim    TABLE     Y   CREATE TABLE public.bim (
    crate_id character varying NOT NULL,
    bim_info jsonb
);
    DROP TABLE public.bim;
       public         heap    postgres    false            �            1259    16686    indoor_system_metadata    TABLE     k   CREATE TABLE public.indoor_system_metadata (
    system_name character varying NOT NULL,
    info jsonb
);
 *   DROP TABLE public.indoor_system_metadata;
       public         heap    postgres    false            �            1259    16692    sensors    TABLE     ^   CREATE TABLE public.sensors (
    acp_id character varying NOT NULL,
    sensor_info jsonb
);
    DROP TABLE public.sensors;
       public         heap    postgres    false                      0    16674    bim 
   TABLE DATA           1   COPY public.bim (crate_id, bim_info) FROM stdin;
    public          postgres    false    203   `                 0    16686    indoor_system_metadata 
   TABLE DATA           C   COPY public.indoor_system_metadata (system_name, info) FROM stdin;
    public          postgres    false    204   z                 0    16692    sensors 
   TABLE DATA           6   COPY public.sensors (acp_id, sensor_info) FROM stdin;
    public          postgres    false    205          �
           2606    16699    bim bim_pkey 
   CONSTRAINT     P   ALTER TABLE ONLY public.bim
    ADD CONSTRAINT bim_pkey PRIMARY KEY (crate_id);
 6   ALTER TABLE ONLY public.bim DROP CONSTRAINT bim_pkey;
       public            postgres    false    203            �
           2606    16703 =   indoor_system_metadata indoor_system_metadata_system_name_key 
   CONSTRAINT        ALTER TABLE ONLY public.indoor_system_metadata
    ADD CONSTRAINT indoor_system_metadata_system_name_key UNIQUE (system_name);
 g   ALTER TABLE ONLY public.indoor_system_metadata DROP CONSTRAINT indoor_system_metadata_system_name_key;
       public            postgres    false    204            �
           2606    16705    sensors metadata_pkey 
   CONSTRAINT     W   ALTER TABLE ONLY public.sensors
    ADD CONSTRAINT metadata_pkey PRIMARY KEY (acp_id);
 ?   ALTER TABLE ONLY public.sensors DROP CONSTRAINT metadata_pkey;
       public            postgres    false    205               
  x�ݓ1k�0���W�j�kKV:�E^��]
F�T#�%#+C��}J�
%��n8��}<^%�vHvSf��f����t�1Js�S48��[9j�Go��Χ��u� �yt��!�98磭��y3���˗B���m��~S;��)9.�E�>'���/�b��zB�D�<@M�#x���P�ǠН�2~�B���^DN#(�/ȷB��D=T��T��Ђ��a*�M� sa�vcel�7��>˱�F�x>VI�|���         �   x�m��
�0E��W�>kH�&��A�a)hTd�n;���97��y����H q����@�&���Q�L��jvM9M՛���S.u`�!�h[J�/�����F�/�9�LsV< -��n��(a-���R�(�Gs c�e�;�         �  x���n�0���S:�qQo��>5(�C/��%���T'Ȼw(g�����A}��p��ϟ��MWv�uS��:t6�`&ӄ���sƨ���mK�Y���2�'%A~��]�����s�*?�4�u��I�L9g�Md�su9d)��t�뮂�(X5v�mW� ?�ʙ�,��((�+\������gkm���ά��'FA�s�b�ne��O]�vca��m���]�*�G��6(?d$&I���t��i�!�L7�5�[h(�,�ܧ���2NF�S��B�49@��=�=bS�9S]�)Jp��1d�ƒc���2D��F�q�.���X�(X�[�;����I�����KF;(0�1>�$1M1�$��~B2bL��d��8 2&c�����,dL'h��ޗ����-�� 'V�Sӕ�|��cBQp���Q�Qp|�n����04�F�������Z�Q���K�YA�g�(ښmo�:WN��	�R���z�p�ǮU뚲[��i�)cO������x��^��`�҇S��6~�((܏��}i�Q�|~Ϳ��RB2V���$�������mݗr��1�Tƈ
,���?w�]���+�$�o"��F������Rot��h-'�D���P����mW�oks����:h��%ys�[�u�Φ�ڝ.�;���s�{0J�CQ᎐�^�x[バC�d*�_Z�O&�?���     