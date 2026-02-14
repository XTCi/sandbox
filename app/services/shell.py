import asyncio
import codecs
import getpass
import logging
import os
import re
import socket
import uuid
from typing import Dict, Optional, List

from app.interfaces.errors.exceptions import AppException, BadRequestException, NotFoundException
from app.models.shell import ConsoleRecord, Shell, ShellExecuteResult, ShellKillResult, ShellReadResult, ShellWaitResult, ShellWriteResult
logger = logging.getLogger(__name__)

class ShellService:
    """shell的服务"""
    active_shells: Dict[str, Shell]
    def __init__(self) -> None:
        self.active_shells = {}
    @classmethod
    def create_session_id(cls) -> str:
        """创建会话id，使用uuid4"""
        session_id = str(uuid.uuid4())
        logger.info(f"创建一个新的Shell会话ID：{session_id}")
        return session_id
    @classmethod
    def _get_display_path(cls, path: str) -> str:
        """将～替换为主目录"""
        home_dir = os.path.expanduser("~")
        logger.debug(f"主目录：{home_dir},路径：{path}")
        # 判断传来的是否是住路径
        if path.startswith(home_dir):
            return path.replace(home_dir, "~", 1)
        return path
    def _format_ps1(self, exec_dir: str) -> str:
        """格式化命令结构提示，增强交互体验"""
        username= getpass.getuser()
        hostname = socket.gethostname()
        display_dir = self._get_display_path(exec_dir)
        return f"{username}@{hostname}:{display_dir} $"
    @classmethod
    async def _create_process(cls, exec_dir: str, command: str) -> asyncio.subprocess.Process:
        """根据传递的执行目录+命令创建一个asyncio管理的子进程"""
        logger.debug(f"在目录{exec_dir}下使用命令{command}创建一个子进程")
        shell_exec= "/bin/bash"
        # 创建一个系统级的子进程执行shell命令
        return await asyncio.create_subprocess_shell(
            command,
            executable=shell_exec,
            cwd=exec_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            stdin=asyncio.subprocess.PIPE,
            limit=1024* 1024,
        )
    async def _start_output_reader(self, session_id: str, process: asyncio.subprocess.Process) -> None:
        """启动写成连续读取进程输出并将其存储到会话中"""
        # 使用统一utf-8
        logger.debug(f"正在启用输出读取器：{session_id}")
        encoding = "utf-8"
        # 创建赠量编码器
        decoder = codecs.getincrementaldecoder(encoding)(errors="replace")

        shell = self.active_shells.get(session_id)
        while True:
            # 判断子进程是否又标准版输出管道
            if process.stdout:
                try:
                    # 读取缓存区的数据，假设一次读取4096
                    buffer = await process.stdout.read(4096)
                    if not buffer:
                        break
                    # 使用编码器进行编码，同时设置final=false表示未结束
                    output = decoder.decode(buffer, final=False)
                    # 判断会话是否存在
                    if shell:
                        shell.output += output
                        if shell.console_records:
                            shell.console_records[-1].output += output
                except Exception as e:
                    logger.error(f"读取进程输出出错：{str(e)}")
                    break
            else:
                break
        logger.debug(f"会话{session_id}的输出读取器已完成")
    async def wait_process(self, session_id: str, seconds: Optional[int] = None) -> ShellWaitResult:
        """传递会话Id+时间，等待子进程结束"""
        logger.debug(f"正在Shell会话中等待进程：{session_id},超时：{seconds}s")
        if session_id not in self.active_shells:
            logger.error(f"Shell会话不存在：{session_id}")
            raise NotFoundException(f"Shell会话不存在：{session_id}")
        # 获取会话和子进程
        shell = self.active_shells[session_id]
        process = shell.process

        try:
            seconds = 60 if seconds is None or seconds <= 0 else seconds
            await asyncio.wait_for(process.wait(),timeout=seconds)
            # 记录日志并发你结果
            logger.info(f"进程已完成，返回代码为：{process.returncode}")
            return ShellWaitResult(returncode=process.returncode)
        except asyncio.TimeoutError:
            logger.warning(f"Shell会话进程等待超时：{seconds}s")
            raise BadRequestException(f"Shell会话进程等待超时：{seconds}s")
        except Exception as e:
            logger.error(f"Shell会话进程等待过程出错：{str(e)}")
            raise AppException(f"shell会话进程等待出错：{seconds}s")
    @classmethod
    def _remove_ansi_escape_codes(cls, text: str) -> str:
        """从文本中删除ANSI转意字符"""
        assi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return assi_escape.sub("", text)

    def get_console_records(self, session_id: str) -> List[ConsoleRecord]:
        """从指定会话中获取控制台记录"""
        # 判断会话是否存在
        logger.debug(f"正在获取Shell会话的控制台记录：{session_id}")
        if session_id not in self.active_shells:
            logger.error(f"shell会话不存在：{session_id}")
            raise NotFoundException(f"shell会话不存在：{session_id}")
        # 获取原始的控制台记录列表
        console_records = self.active_shells[session_id].console_records
        clean_console_records = []

        for console_record in console_records:
            clean_console_records.append(ConsoleRecord(
                ps1=console_record.ps1,
                command=console_record.command,
                output=self._remove_ansi_escape_codes(console_record.output)
            ))
        return clean_console_records



    async def read_shell_output(self, session_id: str, console: bool = False) -> ShellReadResult:
        """根据传递的会话id+是否输出控制台记录获取Shell命令结果"""
        # 判断下传递的会话是否存在
        logger.debug(f"查看shell会话那天：{session_id}")
        if session_id not in self.active_shells:
            logger.error(f"shell会话不存在：{session_id}")
            raise NotFoundException(f"Shell会话不存在：{session_id}")
        # 获取会话
        shell = self.active_shells[session_id]

        # 获取原声输出并移除额外字符
        raw_out= shell.output
        clean_output = self._remove_ansi_escape_codes(raw_out)
        # 判断是否获取控制台记录
        if console:
            console_records = self.get_console_records(session_id)
        else:
            console_records = []
        return ShellReadResult(
            session_id=session_id,
            output=clean_output,
            console_records=console_records
        )
    async def exec_command(
            self,
            session_id: str,
            exec_dir: Optional[str],
            command: str,
    ) -> ShellExecuteResult:
        """传递会话id+执行目录+命令执行后返回结果"""
        logger.info(f"正在会话{session_id}中执行命令：{command}")
        if not exec_dir or exec_dir == "":
            exec_dir = os.path.expanduser("~")
        if not os.path.exists(exec_dir):
            logger.error(f"当前目录不存在：{exec_dir}")
            raise BadRequestException(f"当前目录不存在：{exec_dir}")
        try:
            # 格式化成ps1格式
            ps1 = self._format_ps1(exec_dir)

            # 判断当前Shell会话是否存在
            if session_id not in self.active_shells:
                # 不在就创建一个新的进程
                logger.debug(f"创建一个新的Shell会话：{session_id}")
                process = await self._create_process(exec_dir,command)
                self.active_shells[session_id] = Shell(
                    process=process,
                    exec_dir=exec_dir,
                    output="",
                    console_records=[ConsoleRecord(ps1=ps1,command=command,output="")]
                )
                # 创建后台任务来运行输出读取器
                await asyncio.create_task(self._start_output_reader(session_id, process))
            else:
                # 该会话已存在直接读取
                logger.debug(f"使用现有的shell会话")
                shell = self.active_shells[session_id]
                old_process = shell.process
                # 判断旧进程是否还在运行，如果在运行，则停止就进程在执行新命令
                if old_process.returncode is None:
                    logger.debug(f"正在终止上一个进程:{session_id}")
                    try:
                        old_process.terminate()
                        await asyncio.wait_for(old_process.wait(), timeout=1)
                    except Exception as e:
                        logger.warning(f"强制终止Shell会话中的进程{session_id}失败：{str(e)}")
                        old_process.kill()
                # 关闭之后创建一个新的进程
                process = await self._create_process(exec_dir, command)

                # 更新会话信息
                shell.process = process
                shell.exec_dir = exec_dir
                shell.output = ""
                shell.console_records.append(ConsoleRecord(ps1=ps1, command=command,output=""))
                # 创建后台任务来运行输出读取器
                await asyncio.create_task(self._start_output_reader(session_id,process))

                try:
                    logger.debug(f"正在等待会话中的进程完成：{session_id}")
                    wait_result = await self.wait_process(session_id, seconds=5)

                    # 判断返回的代码是否非空（已经结束）则同步返回执行结果
                    if wait_result.returncode is not None:
                        # 记录日志并查看结果
                        logger.debug(f"Shell会话进程已结束，代码：{wait_result.returncode}")
                        view_result = await self.read_shell_output(session_id)
                        return ShellExecuteResult(
                            session_id=session_id,
                            command=command,
                            status="completed",
                            returncode=wait_result.returncode,
                            output=view_result.output,
                        )
                except BadRequestException as _:
                    logger.warning(f"进程在会话超时后仍在运行：{session_id}")
                    pass
                except Exception as e:
                    logger.warning(f"等待进程出现异常：{str(e)}")
                    pass

                return ShellExecuteResult(
                    session_id=session_id,
                    command=command,
                    status="running"
                )

        except Exception as e:
            logger.error(f"命令执行失败:{str(e)}",exc_info=True)
            raise AppException(
                msg=f"命令执行失败：{str(e)}",
                data={"seesion_id": session_id, "command": command}
            )

    async def write_shell_input(
            self,
            session_id: str,
            input_text: str,
            press_enter: bool
    ) -> ShellWriteResult:
        """根据传递的会话id+输入数据向子进程写入数据"""
        # 判断下会话是否存在
        if session_id not in self.active_shells:
            logger.error(f"Shell会话不存在：{session_id}")
            raise NotFoundException(f"Shell会话不存在：{session_id}")
        shell = self.active_shells[session_id]
        process = shell.process

        try:
            # 检查子进程是否结束
            if process.returncode is not None:
                logger.error(f"子进程已结束，无法写入输入：{session_id}")
                raise BadRequestException(f"子进程已结束，无法写入输入：{session_id}")
            # 统一使用utf-8
            encoding = "utf-8"
            line_ending = "\n"

            # 准备要发送的内容
            text_to_send = input_text
            if press_enter:
                text_to_send += line_ending
            # 将字符串编码为字节流
            input_data = text_to_send.encode(encoding)
            log_text = input_text + ("\n" if press_enter else "")
            shell.output += log_text
            if shell.console_records:
                shell.console_records[-1].output += log_text

            # 向子进程写入数据
            process.stdin.write(input_data)
            await process.stdin.drain()
            # 记录日志并返回写入结果
            logger.info("成功向子进程写入结果")
            return ShellWriteResult(
                status="success"
            )
        except UnicodeError as e:
            logger.error(f"编码错误：{str(e)}")
            raise AppException(f"编码错误：{str(e)}")
        except Exception as e:
            logger.error(f"向子进程写入数据出错：{str(e)}")
            raise AppException(f"向子进程写入数据出错：{str}")


    async def kill_process(self, session_id: str) -> ShellKillResult:
        """根据传递分会话id关闭对应进程"""
        if session_id not in self.active_shells:
            logger.error(f"Shell会话不存在：{session_id}")
            raise NotFoundException(f"Shell会话不存在：{session_id}")

        shell = self.active_shells[session_id]
        process = shell.process

        try:
            if process.returncode is None:
                logger.info(f"优雅的终止进程：{session_id}")
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=3)
                except asyncio.TimeoutError as _:
                    logger.warning(f"尝试强制关闭进程：{session_id}")
                    process.kill
                logger.info(f"进程已经终止，返回代码为：{process.returncode}")
                return ShellKillResult(
                    status="terminated",
                    returncode=process.returncode
                )
            else:
                logger.info(f"进程已经结束，返回代码为：{process.returncode}")
                return ShellKillResult(
                    status="already_terminated",
                    returncode=process.returncode
                )

        except Exception as e:
            logger.error(f"关闭进程错误：{str(e)}",exc_info=True)
            raise AppException(f"关闭进程错误: {str(e)}")
