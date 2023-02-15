--
-- PostgreSQL database dump
--

-- Dumped from database version 11.5
-- Dumped by pg_dump version 11.5

-- Started on 2023-02-15 01:18:23

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 6 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA public;


ALTER SCHEMA public OWNER TO postgres;

--
-- TOC entry 3185 (class 0 OID 0)
-- Dependencies: 6
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS 'standard public schema';


--
-- TOC entry 712 (class 1247 OID 37684800)
-- Name: datos_modelo; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.datos_modelo AS (
	idorden integer,
	desmodelo character varying(250),
	destipocapa character varying(50),
	descapa character varying(50),
	desparametro character varying(150),
	rangoinicio character varying(30),
	rangofin character varying(30),
	idtipodato integer,
	tipodato character varying(100),
	valor character varying(100),
	idmodelocapaparametro integer,
	idparametro integer,
	valores character varying(50),
	idmodelodetalle integer,
	idmodelodetallecapa integer,
	idpadre integer,
	espadre integer,
	base character varying(15),
	idmodelo integer,
	idpadreorden integer,
	dimension integer,
	idcapa integer
);


ALTER TYPE public.datos_modelo OWNER TO postgres;

--
-- TOC entry 319 (class 1255 OID 37684728)
-- Name: create_table(text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.create_table(text, integer) RETURNS text
    LANGUAGE plpgsql
    AS $_$
DECLARE
    cnt     bigint;
	icount  integer;
	len_table integer;
	reg     RECORD;
	table_script  text;
	detal_script  text;
	insert_script  text;
BEGIN
	table_script  := ' CREATE TABLE ' || $1 || ' ( idred SERIAL, ';
	detal_script  := ' CREATE TABLE ' || $1 || '_det ( idsecuencia SERIAL, idred INTEGER, descripcion text )';
	insert_script := ' INSERT INTO '  || $1 || ' ( ';
	
	len_table = length(table_script);
	
	CREATE TEMP TABLE TMP_HLP AS	
								SELECT min(idorden) as idorden,MAX(tipodato)::CHARACTER VARYING(100) AS tipodato 
								FROM public.datos_modelo_type($2) 
								WHERE LENGTH(tipodato) > 0 
								GROUP BY idmodelodetalle, idparametro, desparametro, rangoinicio, rangofin
								ORDER BY idmodelodetalle, idparametro;
	
	FOR REG IN SELECT (row_number () OVER ())::INTEGER AS id, *	   
			   FROM TMP_HLP LOOP
			  
			   table_script  := table_script || '"' ||TRIM(reg.id::character varying(3)) || '"' || ' ' || 'CHARACTER VARYING(50),' ;
			   insert_script := insert_script || '"' ||TRIM(reg.id::character varying(3)) || '"' || ' ' || ',' ;
			   
    END LOOP;
	
	DROP TABLE TMP_HLP;
	
	if length(table_script) > len_table THEN
		raise notice 'Value: %', 1;
		table_script  := substring(table_script,1,length(table_script)-1) || ' , parametros INTEGER, kappa NUMERIC(12,8), acc NUMERIC(12,8), inicio TIMESTAMP WITH TIME ZONE, 
						 fin TIMESTAMP WITH TIME ZONE, idmodelo INTEGER, idnodo INTEGER, idgpu INTEGER, mainpid INTEGER, pid INTEGER, nt_parametros INTEGER)';
		insert_script := substring(insert_script,1,length(insert_script)-1) || ') VALUES ';
	else
		raise notice 'Value: %', 2;
		table_script  := table_script  || ' parametros INTEGER, kappa NUMERIC(12,8), acc NUMERIC(12,8), inicio TIMESTAMP WITH TIME ZONE, 
						 fin TIMESTAMP WITH TIME ZONE, idmodelo INTEGER, idnodo INTEGER, idgpu INTEGER, mainpid INTEGER, pid INTEGER, nt_parametros INTEGER)';
		insert_script := insert_script || ' idmodelo) VALUES ';
		raise notice 'TABLE: %', table_script;
		raise notice 'INSERT: %', insert_script;
	end if;	
	EXECUTE table_script;
	EXECUTE detal_script;
    RETURN insert_script;
END;
$_$;


ALTER FUNCTION public.create_table(text, integer) OWNER TO postgres;

--
-- TOC entry 306 (class 1255 OID 37684801)
-- Name: datos_modelo_type(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.datos_modelo_type(integer) RETURNS SETOF public.datos_modelo
    LANGUAGE plpgsql
    AS $_$
DECLARE
    reg RECORD;
BEGIN
	-- MODELO COMPLETO
	CREATE TEMP TABLE AYUDA AS
								SELECT  a.descripcion as des_a, c.descripcion as des_b,e.descripcion as des_c,h.descripcion as des_d,f.rangoinicio,f.rangofin,f.idtipodato,
										CASE WHEN f.idtipodato in (1, 3, 4, 5, 7) 
											THEN 
												 'Integer(' || TRIM(f.rangoinicio) || ',' || TRIM(f.rangofin) || ')'
											ELSE 
												 'Real('  || TRIM(f.rangoinicio) || ',' || TRIM(f.rangofin) || ')' 
											END::CHARACTER VARYING(100) AS tipodato, f.base,f.idmodelocapaparametro,h.idparametro,g.valores,b.idmodelodetalle,
											f.idmodelodetallecapa,a.idmodelo,g.dimension,e.idcapa,c.idcapaseleccion
									FROM modelo a left join modelodetalle       b  on a.idmodelo            = b.idmodelo
												  left join capaseleccion       c  on b.idcapaseleccion     = c.idcapaseleccion  
												  left join modelodetallecapa   d  on b.idmodelodetalle     = d.idmodelodetalle
												  left join capas               e  on d.idcapa              = e.idcapa
												  left join modelocapaparametro f  on d.idmodelodetallecapa = f.idmodelodetallecapa  
												  left join parametroscapa      g  on f.idparametrocapa     = g.idparametrocapa 
												  left join parametros          h  on g.idparametro         = h.idparametro 
								where a.idmodelo = $1
								order by b.idmodelo,c.idcapaseleccion,d.idmodelodetalle,e.idcapa,f.idmodelodetallecapa,h.descripcion;

	--select * 
	--from ayuda
	--where idmodelodetallecapa = 51;
	
	-- PARAMETROS QUE TIENEN SUBPARAMETROS Y NO SE UILIZAN (AYUDA2 Y AYUDA3)
	CREATE TEMP TABLE AYUDA2 AS
								select idparametro
								from ayuda
								WHERE TRIM(rangoinicio) = TRIM(rangofin) AND TRIM(rangoinicio)='0'
								GROUP BY idparametro
								order by idparametro;

	--select * from ayuda2;
	
	CREATE TEMP TABLE AYUDA3 AS
								select idparametro 
								from ayuda2
								UNION ALL
								select numero as idparametro
								from parametrosdetalle
								where idparametro in (select idparametro from ayuda2) and descripcion is null
								order by idparametro;

	--select * from ayuda3;
	--ELIMINA SUBPARAMETROS QUE NO SE UTILIZAN
	CREATE TEMP TABLE AYUDA4 AS
								SELECT * 
								FROM ayuda
								WHERE idparametro not in (select idparametro from ayuda3);
								
	--select * from ayuda4;				
	
	-- AQUELLOS QUE TIENEN SUBPARAMETROS QUE TIENEN UN VALOR FIJO LES ASIGNA(AYUDA5 Y AYUDA6)
	CREATE TEMP TABLE AYUDA5 AS
								SELECT *
								FROM AYUDA4 
								WHERE TRIM(rangoinicio) = TRIM(rangofin) AND 
									  idparametro IN (SELECT idparametro from parametrosdetalle);
	
	CREATE TEMP TABLE AYUDA6 AS
								SELECT a.*,b.descripcion 
								FROM ayuda5 a LEFT JOIN PARAMETROSDETALLE b ON a.IDPARAMETRO = b.IDPARAMETRO  AND 
														CAST(coalesce(a.rangofin, '0') AS integer) = b.numero;
	--select * 
	--from ayuda6
	--where idmodelodetallecapa = 51;
    ---
	CREATE TEMP TABLE AYUDA7 AS
								select a.*, a.rangofin as descripcion
								from ayuda a left join ayuda6 b on a.idmodelocapaparametro = b.idmodelocapaparametro 
								where a.rangoinicio = a.rangofin and coalesce(b.descripcion,'') = '' and TRIM(a.rangoinicio) != '0';

	--select * 
    --from ayuda7
    --where idmodelodetallecapa = 51;
	
	CREATE TEMP TABLE AYUDA8 AS
								select a.*,case when b.descripcion is not null 
												THEN
													b.descripcion
												ELSE
													c.descripcion
												END	
								from ayuda4 a left join ayuda6 b on a.idmodelocapaparametro = b.idmodelocapaparametro
											  left join ayuda7 c on a.idmodelocapaparametro = c.idmodelocapaparametro
								order by a.idmodelodetalle,a.idcapaseleccion,a.idmodelodetallecapa,a.des_d;	
	
	--select * 
    --from ayuda8
    --where idmodelodetallecapa = 51;
	
	CREATE TEMP TABLE AYUDA9 AS
								select *  
								from parametrosdetalle 
								where  coalesce(descripcion,'') = ''
								order by idparametro,numero;
	
	--select * 
    --from ayuda9;
	
	CREATE TEMP TABLE AYUDA10 AS
								select a.*,coalesce(b.idparametro,0) as idpadre
								from AYUDA8 a left join AYUDA9 b on a.idparametro = b.numero;

	--select * 
    --from ayuda10	
	--where idmodelodetallecapa = 51;
	
	CREATE TEMP TABLE AYUDA11 AS
								select  des_a as desmodelo, des_b as destipocapa, des_c as descapa, des_d as desparametro, 
								rangoinicio, rangofin, idtipodato,
								CASE WHEN rangoinicio = rangofin 
									THEN 
										'' 
									ELSE 
										tipodato END::CHARACTER VARYING(100) AS tipodato, coalesce(descripcion,'')::CHARACTER VARYING(100) as valor, idmodelocapaparametro, 
								idparametro, valores, idmodelodetalle, idmodelodetallecapa, idpadre, base,idmodelo,dimension,idcapa
								from ayuda10
								order by idmodelodetalle,idcapaseleccion,idmodelodetallecapa, des_d;	
								
	--select * 
    --from ayuda11	
	--where idmodelodetallecapa = 51;
	
	CREATE TEMP TABLE AYUDA12 AS
								select (row_number () OVER ())::INTEGER AS idorden,*
								from ayuda11;
								
	CREATE TEMP TABLE AYUDA13 AS
								select idparametro 
								from parametrosdetalle 
								where  coalesce(descripcion,'') = ''
								group by idparametro
								order by idparametro;
	
	--select * 
    --from ayuda13;
	
	
	CREATE TEMP TABLE AYUDA14 AS
								select  a.*,coalesce(b.idparametro,0) as espadre
								from AYUDA12 a left join AYUDA13 b on a.idparametro = b.idparametro
								order by idorden;
								
	--select * 
    --from ayuda14	
	--where idmodelodetallecapa = 51;
	
	----
	CREATE TEMP TABLE AYUDA15 AS							
								SELECT idmodelo,idmodelodetallecapa,idmodelodetalle,idorden,espadre,idpadre
								from  AYUDA14
								where idmodelo = $1  and espadre != 0 -- 
								group by idmodelo,idmodelodetallecapa,idmodelodetalle,idorden,espadre,idpadre
								order by idorden;
	
	--select * 
    --from ayuda15
	--where idmodelodetalle = 49;
	
	
	CREATE TEMP TABLE AYUDA16 AS	
								select a.idorden, a.desmodelo, a.destipocapa, a.descapa, a.desparametro, a.rangoinicio, a.rangofin, 
								a.idtipodato, a.tipodato, a.valor, a.idmodelocapaparametro, a.idparametro, a.valores, a.idmodelodetalle, 
								a.idmodelodetallecapa, a.idpadre, a.espadre, a.base, a.idmodelo,coalesce(b.idorden,0) as idpadreorden,
								a.dimension, a.idcapa
								from  AYUDA14  a left join AYUDA15 b on a.idmodelo            = b.idmodelo           and 
								                                        a.idmodelodetalle     = b.idmodelodetalle     and 
																		a.idmodelodetallecapa = b.idmodelodetallecapa and 
																		a.idpadre             = b.espadre
								order by a.idorden;								
	
	--select *
    --from ayuda16	
	
	--AQUELLOS QUE SON RANGO DE CAPAS
	CREATE TEMP TABLE AYUDA17 AS
								select idmodelodetalle
								from (select idmodelodetalle, idmodelodetallecapa, count(*)
									  from ayuda16	
									  group by idmodelodetalle,idmodelodetallecapa
									  order by idmodelodetalle, idmodelodetallecapa) as atoto
								group by idmodelodetalle	
								having count(*)	> 1;
	
	
	CREATE TEMP TABLE AYUDA18 AS
								select min(idorden) as idorden, min(desmodelo) as desmodelo, min(destipocapa) as destipocapa,
								idmodelo,idmodelodetalle,idmodelodetallecapa
								from AYUDA16
								where idmodelodetalle in (select idmodelodetalle from AYUDA17) 
								group by idmodelo,idmodelodetalle,idmodelodetallecapa
								order by idmodelo,idmodelodetalle,idmodelodetallecapa;

	--select * from ayuda18;
	
	CREATE TEMP TABLE AYUDA19 AS
								select min(idorden)-1 as idorden,min(desmodelo) as desmodelo, min(destipocapa) as destipocapa, 
								idmodelo,idmodelodetalle,count(*) as cantidad
								from  AYUDA18
								group by idmodelo,idmodelodetalle
								having count(*) > 1
								order by idmodelo,idmodelodetalle;

	CREATE TEMP TABLE AYUDA20 AS 
								select *,(row_number () OVER ())::INTEGER AS idhlp 
								from ayuda19
								order by idmodelo,idmodelodetalle;

	CREATE TEMP TABLE AYUDA21 AS
								select idorden, desmodelo::CHARACTER VARYING(250), destipocapa::CHARACTER VARYING(50), 
								'Types'::CHARACTER VARYING(50) as descapa, 'Types'::CHARACTER VARYING(150) as desparametro,
								1::CHARACTER VARYING(30) as rangoinicio, cantidad::CHARACTER VARYING(30) as rangofin, 
								1 as idtipodato, ('Integer(1,'||cantidad::CHARACTER VARYING(100)||')')::CHARACTER VARYING(100) as tipodato,''::CHARACTER VARYING(100) as valor, 
								0 as idmodelocapaparametro, 0 as idparametro,''::CHARACTER VARYING(50) as valores,
								idmodelodetalle, 0 as idmodelodetallecapa, 0 as idpadre, 0 as espadre,
								'0'::CHARACTER VARYING(15) as base,idmodelo, 0 as idpadreorden, 0 as dimension, 0 as idcapa
								from AYUDA19;						

	CREATE TEMP TABLE AYUDA22 AS
								SELECT *
								from  AYUDA16
								UNION
								select *
								from AYUDA21
								order by idorden,idmodelodetalle;

	CREATE TEMP TABLE AYUDA23 AS
								select a.idorden, a.desmodelo, a.destipocapa, a.descapa, a.desparametro,
									   a.rangoinicio, a.rangofin, a.idtipodato, a.tipodato,valor, a.idmodelocapaparametro, a.idparametro
									   ,a.valores,  a.idmodelodetalle, a.idmodelodetallecapa, a.idpadre, a.espadre, a.base, a.idmodelo, 
									   CASE WHEN a.idpadreorden > 0 
											THEN
												a.idpadreorden + coalesce(b.idhlp,0)
											ELSE
												a.idpadreorden
									   END as idpadreorden, a.dimension, 
									   a.idcapa
								from ayuda22 A LEFT JOIN AYUDA20 B ON A.IDMODELODETALLE=B.IDMODELODETALLE  
								order by idorden,idmodelodetalle;	
	
	CREATE TEMP TABLE AYUDA24 AS
								select (row_number () OVER ())::INTEGER AS idorden, desmodelo, destipocapa, descapa,desparametro,
								rangoinicio, rangofin, idtipodato, tipodato,valor, idmodelocapaparametro, idparametro,valores, 
								idmodelodetalle, idmodelodetallecapa, idpadre, espadre, base,idmodelo, idpadreorden, dimension, 
								idcapa
								from AYUDA23;
	
    
	FOR REG IN SELECT idorden,desmodelo, destipocapa, descapa, desparametro, rangoinicio, rangofin, idtipodato, tipodato, valor, idmodelocapaparametro, 
					  idparametro, valores, idmodelodetalle, idmodelodetallecapa, idpadre, espadre, base,idmodelo,idpadreorden,dimension,idcapa
		       FROM AYUDA24 LOOP
       RETURN NEXT reg;
    END LOOP;
	
	DROP TABLE AYUDA;
	DROP TABLE AYUDA2;
	DROP TABLE AYUDA3;
	DROP TABLE AYUDA4;
	DROP TABLE AYUDA5;
	DROP TABLE AYUDA6;
	DROP TABLE AYUDA7;
	DROP TABLE AYUDA8;
	DROP TABLE AYUDA9;
	DROP TABLE AYUDA10;
	DROP TABLE AYUDA11;
	DROP TABLE AYUDA12;
	DROP TABLE AYUDA13;
	DROP TABLE AYUDA14;
	DROP TABLE AYUDA15;
	DROP TABLE AYUDA16;
	DROP TABLE AYUDA17;
	DROP TABLE AYUDA18;
	DROP TABLE AYUDA19;
	DROP TABLE AYUDA20;
	DROP TABLE AYUDA21;
	DROP TABLE AYUDA22;
	DROP TABLE AYUDA23;
	DROP TABLE AYUDA24;
	RETURN;
	

END
$_$;


ALTER FUNCTION public.datos_modelo_type(integer) OWNER TO postgres;

--
-- TOC entry 236 (class 1259 OID 37685218)
-- Name: capas_idcapa_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.capas_idcapa_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE public.capas_idcapa_seq OWNER TO postgres;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- TOC entry 237 (class 1259 OID 37685220)
-- Name: capas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.capas (
    idcapa integer DEFAULT nextval('public.capas_idcapa_seq'::regclass) NOT NULL,
    idtipocapa integer,
    descripcion character varying(50),
    evaluar integer
);


ALTER TABLE public.capas OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 37684905)
-- Name: capaseleccion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.capaseleccion (
    idcapaseleccion integer NOT NULL,
    descripcion character varying(50)
);


ALTER TABLE public.capaseleccion OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 37684903)
-- Name: capaseleccion_idcapaseleccion_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.capaseleccion_idcapaseleccion_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.capaseleccion_idcapaseleccion_seq OWNER TO postgres;

--
-- TOC entry 3186 (class 0 OID 0)
-- Dependencies: 226
-- Name: capaseleccion_idcapaseleccion_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.capaseleccion_idcapaseleccion_seq OWNED BY public.capaseleccion.idcapaseleccion;


--
-- TOC entry 248 (class 1259 OID 37698094)
-- Name: eegnet_ideegnet_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.eegnet_ideegnet_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE public.eegnet_ideegnet_seq OWNER TO postgres;

--
-- TOC entry 249 (class 1259 OID 37698096)
-- Name: eegnet; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.eegnet (
    ideegnet integer DEFAULT nextval('public.eegnet_ideegnet_seq'::regclass) NOT NULL,
    item integer,
    epochs integer,
    early_stop integer,
    kappa numeric(32,16),
    accuracy numeric(32,16),
    exe_ini timestamp with time zone,
    exe_end timestamp without time zone,
    idmuestra integer,
    bits integer
);


ALTER TABLE public.eegnet OWNER TO postgres;

--
-- TOC entry 215 (class 1259 OID 37684644)
-- Name: ejecuciones_idejecucion_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ejecuciones_idejecucion_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE public.ejecuciones_idejecucion_seq OWNER TO postgres;

--
-- TOC entry 216 (class 1259 OID 37684646)
-- Name: ejecuciones; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ejecuciones (
    idejecucion integer DEFAULT nextval('public.ejecuciones_idejecucion_seq'::regclass) NOT NULL,
    idexperimento integer,
    idnodo integer,
    idgpu integer,
    item integer,
    tabla character varying(150),
    archivo character varying(150),
    mainpid integer,
    pid integer,
    codo_nd_param integer,
    codo_nd_kappa numeric(32,16),
    ga_population integer,
    ga_nfe integer,
    ga_ini timestamp with time zone,
    ga_end timestamp with time zone,
    idred integer,
    min_param integer,
    max_param integer,
    min_kappa numeric(32,16),
    max_kappa numeric(32,16),
    hypervolumen numeric(32,16),
    stdv_knee_kappa numeric(32,16),
    avg_knee_kappa numeric(32,16)
);


ALTER TABLE public.ejecuciones OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 37684732)
-- Name: experimentos_idexperimento_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.experimentos_idexperimento_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE public.experimentos_idexperimento_seq OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 37684734)
-- Name: experimentos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.experimentos (
    idexperimento integer DEFAULT nextval('public.experimentos_idexperimento_seq'::regclass) NOT NULL,
    idmodelo integer,
    idmuestra integer,
    ejecuciones integer,
    total integer,
    ga_population integer,
    ga_nfe integer,
    ga_sbx numeric(4,2),
    ga_pm numeric(4,2),
    cnn_max_parameters integer,
    cnn_epochs integer,
    idparallel_level integer
);


ALTER TABLE public.experimentos OWNER TO postgres;

--
-- TOC entry 240 (class 1259 OID 37696481)
-- Name: gpus_idgpu_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.gpus_idgpu_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE public.gpus_idgpu_seq OWNER TO postgres;

--
-- TOC entry 241 (class 1259 OID 37696483)
-- Name: gpus; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.gpus (
    idgpu integer DEFAULT nextval('public.gpus_idgpu_seq'::regclass) NOT NULL,
    idnodo integer,
    number integer,
    name character varying(150),
    memory character varying(150),
    utilizado integer,
    activo integer
);


ALTER TABLE public.gpus OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 37684824)
-- Name: modelo_idmodelo_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.modelo_idmodelo_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE public.modelo_idmodelo_seq OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 37684826)
-- Name: modelo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.modelo (
    idmodelo integer DEFAULT nextval('public.modelo_idmodelo_seq'::regclass) NOT NULL,
    descripcion character varying(250),
    cantidadcapas integer,
    abreviatura character varying(15),
    parametros integer
);


ALTER TABLE public.modelo OWNER TO postgres;

--
-- TOC entry 230 (class 1259 OID 37685001)
-- Name: modelodetallecapaparametro_idmodelodetallecapaparametro_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.modelodetallecapaparametro_idmodelodetallecapaparametro_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE public.modelodetallecapaparametro_idmodelodetallecapaparametro_seq OWNER TO postgres;

--
-- TOC entry 231 (class 1259 OID 37685003)
-- Name: modelocapaparametro; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.modelocapaparametro (
    idmodelocapaparametro integer DEFAULT nextval('public.modelodetallecapaparametro_idmodelodetallecapaparametro_seq'::regclass) NOT NULL,
    idmodelodetallecapa integer,
    idparametrocapa integer,
    rangoinicio character varying(30),
    rangofin character varying(30),
    idtipodato integer,
    base character varying(15)
);


ALTER TABLE public.modelocapaparametro OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 37684869)
-- Name: modelodetalle_idmodelodetalle_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.modelodetalle_idmodelodetalle_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE public.modelodetalle_idmodelodetalle_seq OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 37684871)
-- Name: modelodetalle; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.modelodetalle (
    idmodelodetalle integer DEFAULT nextval('public.modelodetalle_idmodelodetalle_seq'::regclass) NOT NULL,
    idmodelo integer,
    numero integer,
    idcapaseleccion integer
);


ALTER TABLE public.modelodetalle OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 37684941)
-- Name: modelodetallecapa; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.modelodetallecapa (
    idmodelodetallecapa integer NOT NULL,
    idmodelodetalle integer,
    idcapa integer,
    evaluar integer
);


ALTER TABLE public.modelodetallecapa OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 37684939)
-- Name: modelodetallecapa_idmodelodetallecapa_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.modelodetallecapa_idmodelodetallecapa_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.modelodetallecapa_idmodelodetallecapa_seq OWNER TO postgres;

--
-- TOC entry 3187 (class 0 OID 0)
-- Dependencies: 228
-- Name: modelodetallecapa_idmodelodetallecapa_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.modelodetallecapa_idmodelodetallecapa_seq OWNED BY public.modelodetallecapa.idmodelodetallecapa;


--
-- TOC entry 246 (class 1259 OID 37696653)
-- Name: muestras_idmuestra_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.muestras_idmuestra_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE public.muestras_idmuestra_seq OWNER TO postgres;

--
-- TOC entry 247 (class 1259 OID 37696655)
-- Name: muestras; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.muestras (
    idmuestra integer DEFAULT nextval('public.muestras_idmuestra_seq'::regclass) NOT NULL,
    descripcion character varying(100),
    origen character varying(100),
    activo integer
);


ALTER TABLE public.muestras OWNER TO postgres;

--
-- TOC entry 242 (class 1259 OID 37696489)
-- Name: nodos_idnodo_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.nodos_idnodo_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE public.nodos_idnodo_seq OWNER TO postgres;

--
-- TOC entry 243 (class 1259 OID 37696491)
-- Name: nodos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.nodos (
    idnodo integer DEFAULT nextval('public.nodos_idnodo_seq'::regclass) NOT NULL,
    descripcion character varying(150),
    utilizado numeric(1,0),
    activo numeric(1,0)
);


ALTER TABLE public.nodos OWNER TO postgres;

--
-- TOC entry 234 (class 1259 OID 37685129)
-- Name: parametros_idparametro_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.parametros_idparametro_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE public.parametros_idparametro_seq OWNER TO postgres;

--
-- TOC entry 235 (class 1259 OID 37685131)
-- Name: parametros; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.parametros (
    idparametro integer DEFAULT nextval('public.parametros_idparametro_seq'::regclass) NOT NULL,
    descripcion character varying(150)
);


ALTER TABLE public.parametros OWNER TO postgres;

--
-- TOC entry 232 (class 1259 OID 37685121)
-- Name: parametroscapa_idparametrocapa_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.parametroscapa_idparametrocapa_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE public.parametroscapa_idparametrocapa_seq OWNER TO postgres;

--
-- TOC entry 233 (class 1259 OID 37685123)
-- Name: parametroscapa; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.parametroscapa (
    idparametrocapa integer DEFAULT nextval('public.parametroscapa_idparametrocapa_seq'::regclass) NOT NULL,
    idcapa integer,
    idparametro integer,
    valores character varying(50),
    dimension integer,
    idtipodato integer
);


ALTER TABLE public.parametroscapa OWNER TO postgres;

--
-- TOC entry 238 (class 1259 OID 37685314)
-- Name: parametrosdetalle_idparametrodetalle_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.parametrosdetalle_idparametrodetalle_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE public.parametrosdetalle_idparametrodetalle_seq OWNER TO postgres;

--
-- TOC entry 239 (class 1259 OID 37685316)
-- Name: parametrosdetalle; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.parametrosdetalle (
    idparametrodetalle integer DEFAULT nextval('public.parametrosdetalle_idparametrodetalle_seq'::regclass) NOT NULL,
    idparametro integer,
    numero integer,
    descripcion character varying(150),
    idtipodato integer
);


ALTER TABLE public.parametrosdetalle OWNER TO postgres;

--
-- TOC entry 244 (class 1259 OID 37696591)
-- Name: soluciones_idsolucion_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.soluciones_idsolucion_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE public.soluciones_idsolucion_seq OWNER TO postgres;

--
-- TOC entry 245 (class 1259 OID 37696593)
-- Name: soluciones; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.soluciones (
    idsolucion integer DEFAULT nextval('public.soluciones_idsolucion_seq'::regclass) NOT NULL,
    idejecucion integer,
    parametros integer,
    kappa numeric(32,16)
);


ALTER TABLE public.soluciones OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 37684679)
-- Name: solucionesnd_idsolucion_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.solucionesnd_idsolucion_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE public.solucionesnd_idsolucion_seq OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 37684681)
-- Name: solucionesnd; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.solucionesnd (
    idsolucion integer DEFAULT nextval('public.solucionesnd_idsolucion_seq'::regclass) NOT NULL,
    idejecucion integer,
    parametros integer,
    kappa numeric(32,16)
);


ALTER TABLE public.solucionesnd OWNER TO postgres;

--
-- TOC entry 2979 (class 2604 OID 37684908)
-- Name: capaseleccion idcapaseleccion; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.capaseleccion ALTER COLUMN idcapaseleccion SET DEFAULT nextval('public.capaseleccion_idcapaseleccion_seq'::regclass);


--
-- TOC entry 2980 (class 2604 OID 37684944)
-- Name: modelodetallecapa idmodelodetallecapa; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.modelodetallecapa ALTER COLUMN idmodelodetallecapa SET DEFAULT nextval('public.modelodetallecapa_idmodelodetallecapa_seq'::regclass);

--
-- TOC entry 3188 (class 0 OID 0)
-- Dependencies: 236
-- Name: capas_idcapa_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.capas_idcapa_seq', 1, false);


--
-- TOC entry 3189 (class 0 OID 0)
-- Dependencies: 226
-- Name: capaseleccion_idcapaseleccion_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.capaseleccion_idcapaseleccion_seq', 1, false);


--
-- TOC entry 3190 (class 0 OID 0)
-- Dependencies: 248
-- Name: eegnet_ideegnet_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.eegnet_ideegnet_seq', 1, false);


--
-- TOC entry 3191 (class 0 OID 0)
-- Dependencies: 215
-- Name: ejecuciones_idejecucion_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ejecuciones_idejecucion_seq', 1, false);


--
-- TOC entry 3192 (class 0 OID 0)
-- Dependencies: 219
-- Name: experimentos_idexperimento_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.experimentos_idexperimento_seq', 1, false);


--
-- TOC entry 3193 (class 0 OID 0)
-- Dependencies: 240
-- Name: gpus_idgpu_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.gpus_idgpu_seq', 1, false);


--
-- TOC entry 3194 (class 0 OID 0)
-- Dependencies: 222
-- Name: modelo_idmodelo_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.modelo_idmodelo_seq', 1, false);


--
-- TOC entry 3195 (class 0 OID 0)
-- Dependencies: 224
-- Name: modelodetalle_idmodelodetalle_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.modelodetalle_idmodelodetalle_seq', 1, false);


--
-- TOC entry 3196 (class 0 OID 0)
-- Dependencies: 228
-- Name: modelodetallecapa_idmodelodetallecapa_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.modelodetallecapa_idmodelodetallecapa_seq', 1, false);


--
-- TOC entry 3197 (class 0 OID 0)
-- Dependencies: 230
-- Name: modelodetallecapaparametro_idmodelodetallecapaparametro_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.modelodetallecapaparametro_idmodelodetallecapaparametro_seq', 1, false);


--
-- TOC entry 3198 (class 0 OID 0)
-- Dependencies: 246
-- Name: muestras_idmuestra_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.muestras_idmuestra_seq', 1, false);


--
-- TOC entry 3199 (class 0 OID 0)
-- Dependencies: 242
-- Name: nodos_idnodo_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.nodos_idnodo_seq', 1, false);


--
-- TOC entry 3200 (class 0 OID 0)
-- Dependencies: 234
-- Name: parametros_idparametro_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.parametros_idparametro_seq', 1, false);


--
-- TOC entry 3201 (class 0 OID 0)
-- Dependencies: 232
-- Name: parametroscapa_idparametrocapa_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.parametroscapa_idparametrocapa_seq', 1, false);


--
-- TOC entry 3202 (class 0 OID 0)
-- Dependencies: 238
-- Name: parametrosdetalle_idparametrodetalle_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.parametrosdetalle_idparametrodetalle_seq', 1, false);


--
-- TOC entry 3203 (class 0 OID 0)
-- Dependencies: 244
-- Name: soluciones_idsolucion_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.soluciones_idsolucion_seq', 1, false);


--
-- TOC entry 3204 (class 0 OID 0)
-- Dependencies: 217
-- Name: solucionesnd_idsolucion_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.solucionesnd_idsolucion_seq', 1, false);


--
-- TOC entry 3012 (class 2606 OID 37685225)
-- Name: capas capas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.capas
    ADD CONSTRAINT capas_pkey PRIMARY KEY (idcapa);


--
-- TOC entry 3002 (class 2606 OID 37684910)
-- Name: capaseleccion capaseleccion_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.capaseleccion
    ADD CONSTRAINT capaseleccion_pkey PRIMARY KEY (idcapaseleccion);


--
-- TOC entry 3024 (class 2606 OID 37698101)
-- Name: eegnet eegnet_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.eegnet
    ADD CONSTRAINT eegnet_pkey PRIMARY KEY (ideegnet);


--
-- TOC entry 2992 (class 2606 OID 37684651)
-- Name: ejecuciones ejecuciones_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ejecuciones
    ADD CONSTRAINT ejecuciones_pkey PRIMARY KEY (idejecucion);


--
-- TOC entry 2996 (class 2606 OID 37684739)
-- Name: experimentos experimentos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.experimentos
    ADD CONSTRAINT experimentos_pkey PRIMARY KEY (idexperimento);


--
-- TOC entry 3016 (class 2606 OID 37696488)
-- Name: gpus gpus_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.gpus
    ADD CONSTRAINT gpus_pkey PRIMARY KEY (idgpu);


--
-- TOC entry 2998 (class 2606 OID 37684831)
-- Name: modelo modelo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.modelo
    ADD CONSTRAINT modelo_pkey PRIMARY KEY (idmodelo);


--
-- TOC entry 3000 (class 2606 OID 37684876)
-- Name: modelodetalle modelodetallecapa_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.modelodetalle
    ADD CONSTRAINT modelodetallecapa_pkey PRIMARY KEY (idmodelodetalle);


--
-- TOC entry 3004 (class 2606 OID 37684946)
-- Name: modelodetallecapa modelodetallecapa_pkey1; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.modelodetallecapa
    ADD CONSTRAINT modelodetallecapa_pkey1 PRIMARY KEY (idmodelodetallecapa);


--
-- TOC entry 3006 (class 2606 OID 37685008)
-- Name: modelocapaparametro modelodetallecapaparametro_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.modelocapaparametro
    ADD CONSTRAINT modelodetallecapaparametro_pkey PRIMARY KEY (idmodelocapaparametro);


--
-- TOC entry 3022 (class 2606 OID 37696660)
-- Name: muestras muestras_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.muestras
    ADD CONSTRAINT muestras_pkey PRIMARY KEY (idmuestra);


--
-- TOC entry 3018 (class 2606 OID 37696496)
-- Name: nodos nodos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nodos
    ADD CONSTRAINT nodos_pkey PRIMARY KEY (idnodo);


--
-- TOC entry 3010 (class 2606 OID 37685136)
-- Name: parametros parametros_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parametros
    ADD CONSTRAINT parametros_pkey PRIMARY KEY (idparametro);


--
-- TOC entry 3008 (class 2606 OID 37685128)
-- Name: parametroscapa parametroscapa_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parametroscapa
    ADD CONSTRAINT parametroscapa_pkey PRIMARY KEY (idparametrocapa);


--
-- TOC entry 3014 (class 2606 OID 37685321)
-- Name: parametrosdetalle parametrosdetalle_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parametrosdetalle
    ADD CONSTRAINT parametrosdetalle_pkey PRIMARY KEY (idparametrodetalle);


--
-- TOC entry 3020 (class 2606 OID 37696598)
-- Name: soluciones soluciones_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.soluciones
    ADD CONSTRAINT soluciones_pkey PRIMARY KEY (idsolucion);


--
-- TOC entry 2994 (class 2606 OID 37684686)
-- Name: solucionesnd solucionesnd_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solucionesnd
    ADD CONSTRAINT solucionesnd_pkey PRIMARY KEY (idsolucion);


-- Completed on 2023-02-15 01:18:24

--
-- PostgreSQL database dump complete
--

